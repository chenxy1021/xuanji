"""运行设置：AI 模型的地址、密钥与模型名。

限制与取舍：
- 全站共用一份 AI 配置，只有管理员可读写：未登录 401、已登录非管理员 403。
- 接口只返回「是否配置 / 尾号」，不返回密钥明文。
- 写入落在后端本机 `.local/llm.json`（0600），不经过浏览器存储。
- 匿名可见的信息只经 `/meta`（仅暴露 `llm_configured` 与接口/模型名）。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from app.api.deps import AdminUser
from app.core import llm_store
from app.core.errors import AppError

router = APIRouter(tags=["settings"])


class LlmSettingsIn(BaseModel):
    base_url: str | None = Field(default=None, max_length=300)
    api_key: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=120)
    clear_key: bool = False


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.get("/settings/llm", summary="读取 AI 模型设置（仅管理员）")
def get_llm_settings(response: Response, _admin: AdminUser) -> dict[str, Any]:
    _no_store(response)
    return llm_store.public()


@router.put("/settings/llm", summary="保存 AI 模型设置（仅管理员）")
def put_llm_settings(
    payload: LlmSettingsIn, response: Response, _admin: AdminUser
) -> dict[str, Any]:
    base_url = payload.base_url.strip() if payload.base_url is not None else None
    model = payload.model.strip() if payload.model is not None else None
    api_key = payload.api_key.strip() if payload.api_key is not None else None

    if base_url is not None:
        base_url = base_url.rstrip("/")
        if not llm_store.valid_base_url(base_url):
            raise AppError("invalid_base_url", "接口地址需以 http:// 或 https:// 开头", 422)
    if model is not None and not llm_store.valid_model(model):
        raise AppError("invalid_model", "模型名不能为空，且不能包含空白字符", 422)
    if api_key and any(ch in api_key for ch in "\r\n\t"):
        raise AppError("invalid_api_key", "密钥不能包含换行或制表符", 422)

    info = llm_store.update(
        base_url=base_url,
        api_key=api_key or None,
        model=model,
        clear_key=payload.clear_key,
    )
    _no_store(response)
    return info


@router.delete("/settings/llm", summary="清除运行时 AI 设置（仅管理员）")
def delete_llm_settings(response: Response, _admin: AdminUser) -> dict[str, Any]:
    info = llm_store.reset()
    _no_store(response)
    return info
