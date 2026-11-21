"""运行能力探测：前端据此在 AI 面板提前提示「未配置密钥」。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response

from app.core import llm_store

router = APIRouter(tags=["meta"])


@router.get("/meta")
def meta(response: Response) -> dict[str, Any]:
    info = llm_store.public()
    response.headers["Cache-Control"] = "no-store"
    return {
        "llm_configured": info["configured"],
        "llm_base_url": info["base_url"],
        "llm_model": info["model"],
        "llm_source": info["source"],
        "llm_key_hint": info["key_hint"],
    }
