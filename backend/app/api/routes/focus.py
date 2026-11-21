"""AI 解读方向：前端据此渲染方向标签，提交时只回传 id。"""

from __future__ import annotations

from fastapi import APIRouter

from app.core import focus
from app.domains import get_domain

router = APIRouter(tags=["focus"])


@router.get("/focus/{system}", summary="解读方向目录")
def list_focus(system: str) -> dict:
    get_domain(system)  # 未知体系 404
    return {"system": system, "topics": focus.as_dicts(system)}
