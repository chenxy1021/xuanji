"""AI 解读：SSE 流式输出。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core import focus as focus_catalog
from app.core import llm
from app.core.errors import AppError
from app.core.prompt import build_messages
from app.domains import get_domain

router = APIRouter(tags=["interpret"])


class InterpretRequest(BaseModel):
    system: str
    chart: dict[str, Any]
    text: str | None = None
    question: str | None = Field(default=None, max_length=500)
    style: Literal["concise", "detailed"] = "concise"
    focus: list[Annotated[str, Field(max_length=40)]] = Field(default_factory=list, max_length=20)


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/interpret", summary="AI 解读（SSE 流式）")
async def interpret(payload: InterpretRequest) -> StreamingResponse:
    domain = get_domain(payload.system)  # 未知体系 404
    chart_text = payload.text or domain.render_text(payload.chart)
    messages = build_messages(
        system=payload.system,
        chart_text=chart_text,
        chart_json=json.dumps(payload.chart, ensure_ascii=False),
        question=payload.question,
        style=payload.style,
        focus=focus_catalog.labels_for(payload.system, payload.focus),
    )

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for delta in llm.stream_chat(messages):
                yield _sse("delta", {"text": delta})
            yield _sse("done", {"ok": True})
        except AppError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            yield _sse("error", detail or {"code": "interpret_error", "message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
