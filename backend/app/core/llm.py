"""OpenAI 兼容协议的流式对话客户端。

只依赖 httpx，不绑定具体厂商：DeepSeek / OpenAI / 通义 / 自建网关都可，
用 SM_LLM_BASE_URL + SM_LLM_API_KEY + SM_LLM_MODEL 配置即可。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.core import llm_store
from app.core.config import get_settings
from app.core.errors import AppError


def is_configured() -> bool:
    return bool(llm_store.current().api_key)


async def stream_chat(messages: list[dict[str, str]], temperature: float = 0.7) -> AsyncIterator[str]:
    settings = get_settings()
    cfg = llm_store.current()
    if not cfg.api_key:
        raise AppError(
            "llm_not_configured",
            "未配置 AI 模型密钥，可在「设置 → AI 解读」填写，或设置 SM_LLM_API_KEY",
            503,
        )

    # 容忍用户把完整端点粘贴进「接口地址」
    base = cfg.base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    url = base + "/chat/completions"
    payload = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(settings.llm_timeout, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode("utf-8", "ignore")[:300]
                    raise AppError(
                        "llm_upstream_error",
                        f"模型服务返回 {response.status_code}：{body}",
                        502,
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield content
        except httpx.HTTPError as exc:
            raise AppError("llm_network_error", f"连接模型服务失败：{exc}", 502) from exc
