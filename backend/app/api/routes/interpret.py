"""AI 解读：SSE 流式输出。"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core import focus as focus_catalog
from app.core import llm, llm_store
from app.core.errors import AppError
from app.core.prompt import build_messages
from app.domains import get_domain

router = APIRouter(tags=["interpret"])
logger = logging.getLogger(__name__)


class ClientLlmConfig(BaseModel):
    """浏览器里用户自己的模型配置，仅用于本次请求，不落库。"""

    base_url: str = Field(min_length=1, max_length=300)
    api_key: str = Field(default="", max_length=500)
    model: str = Field(min_length=1, max_length=120)


class InterpretRequest(BaseModel):
    system: str
    chart: dict[str, Any]
    text: str | None = None
    question: str | None = Field(default=None, max_length=500)
    style: Literal["concise", "detailed"] = "concise"
    focus: list[Annotated[str, Field(max_length=40)]] = Field(default_factory=list, max_length=20)
    lang: Literal["zh", "en"] = "zh"
    llm: ClientLlmConfig | None = None


_CJK_RE = re.compile(r"[一-鿿]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def _answer_lang(ui_lang: str, question: str | None) -> str:
    """用户用英文提问就用英文回答；没提问时跟随界面语言。"""
    if question:
        text = question.strip()
        if _CJK_RE.search(text):
            return "zh"
        if len(_LATIN_RE.findall(text)) >= 4:
            return "en"
    return ui_lang


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _client_llm(raw: ClientLlmConfig | None) -> llm_store.LlmConfig | None:
    if raw is None:
        return None
    base_url = raw.base_url.strip().rstrip("/")
    model = raw.model.strip()
    api_key = raw.api_key.strip()
    if not llm_store.valid_base_url(base_url):
        raise AppError("invalid_base_url", "接口地址需以 http:// 或 https:// 开头", 422)
    if not llm_store.valid_model(model):
        raise AppError("invalid_model", "模型名不能为空，且不能包含空白字符", 422)
    if any(ch in api_key for ch in "\r\n\t"):
        raise AppError("invalid_api_key", "密钥不能包含换行或制表符", 422)
    return llm_store.LlmConfig(base_url=base_url, api_key=api_key, model=model, source="client")


@router.post("/interpret", summary="AI 解读（SSE 流式）")
async def interpret(payload: InterpretRequest) -> StreamingResponse:
    domain = get_domain(payload.system)  # 未知体系 404
    cfg = _client_llm(payload.llm)
    lang = _answer_lang(payload.lang, payload.question)
    chart_text = payload.text or domain.render_text(payload.chart)
    messages = build_messages(
        system=payload.system,
        chart_text=chart_text,
        chart_json=json.dumps(payload.chart, ensure_ascii=False),
        question=payload.question,
        style=payload.style,
        focus=focus_catalog.labels_for(payload.system, payload.focus, lang),
        lang=lang,
    )

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for delta in llm.stream_chat(messages, cfg):
                yield _sse("delta", {"text": delta})
            yield _sse("done", {"ok": True})
        except AppError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            yield _sse("error", detail or {"code": "interpret_error", "message": str(exc)})
        except Exception as exc:  # noqa: BLE001 - 生成器里漏出的异常会直接断流，必须收成 SSE 事件
            logger.exception("AI 解读流式生成失败")
            yield _sse(
                "error",
                {"code": "interpret_error", "message": f"解读失败：{type(exc).__name__}: {exc}"},
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
