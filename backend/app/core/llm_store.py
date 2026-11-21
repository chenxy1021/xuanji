"""运行时可修改的模型配置。

优先级：设置页保存的值 > 环境变量 > 默认值。

- 密钥只写不读：对外只返回是否配置和尾号，接口永远不回传明文。
- 保存位置默认 `backend/.local/llm.json`，权限 0600；可用
  `SM_LLM_CONFIG_PATH` 指向别处（测试与容器场景）。
- 这是单机/可信环境的设计；公网部署前应给设置接口加访问控制。
"""

from __future__ import annotations

import json
import os
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / ".local" / "llm.json"
_LOCK = threading.Lock()

_KEY_MAX = 500
_URL_MAX = 300
_MODEL_MAX = 120


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str
    model: str
    source: str  # runtime / env / default


def config_path() -> Path:
    override = os.getenv("SM_LLM_CONFIG_PATH")
    return Path(override) if override else _DEFAULT_PATH


def _clean(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if len(text) > limit or any(ch in text for ch in "\r\n\t"):
        return ""
    return text


def _read() -> dict[str, Any]:
    try:
        raw = json.loads(config_path().read_text("utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def current() -> LlmConfig:
    base = get_settings()
    stored = _read()
    saved_key = _clean(stored.get("api_key"), _KEY_MAX)
    base_url = _clean(stored.get("base_url"), _URL_MAX) or base.llm_base_url
    model = _clean(stored.get("model"), _MODEL_MAX) or base.llm_model
    if saved_key:
        return LlmConfig(base_url=base_url, api_key=saved_key, model=model, source="runtime")
    env_key = base.llm_api_key.strip()
    return LlmConfig(
        base_url=base_url,
        api_key=env_key,
        model=model,
        source="env" if env_key else "default",
    )


def public() -> dict[str, Any]:
    cfg = current()
    # 过短的密钥不显示尾号，避免把整个密钥暴露出去
    hint = f"••••{cfg.api_key[-4:]}" if len(cfg.api_key) >= 12 else ("••••" if cfg.api_key else "")
    return {
        "configured": bool(cfg.api_key),
        "base_url": cfg.base_url,
        "model": cfg.model,
        "source": cfg.source,
        "key_hint": hint,
    }


def valid_base_url(value: str) -> bool:
    return (
        bool(value)
        and len(value) <= _URL_MAX
        and value.startswith(("http://", "https://"))
        and not any(ch.isspace() for ch in value)
    )


def valid_model(value: str) -> bool:
    return bool(value) and len(value) <= _MODEL_MAX and not any(ch.isspace() for ch in value)


def update(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    clear_key: bool = False,
) -> dict[str, Any]:
    """写入运行时配置。None 表示保持原值；api_key 空串同样视为保持。"""
    with _LOCK:
        stored = _read()
        if base_url is not None:
            stored["base_url"] = base_url.rstrip("/")
        if model is not None:
            stored["model"] = model
        if api_key:
            stored["api_key"] = api_key
        if clear_key:
            stored.pop("api_key", None)

        path = config_path()
        if not stored:
            path.unlink(missing_ok=True)
            return public()

        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(stored, ensure_ascii=False, indent=2), "utf-8")
        try:
            tmp.chmod(0o600)
        except OSError:  # 某些文件系统不支持 chmod
            pass
        os.replace(tmp, path)
    return public()


def reset() -> dict[str, Any]:
    with _LOCK:
        config_path().unlink(missing_ok=True)
    return public()


def file_mode() -> int | None:
    try:
        return stat.S_IMODE(config_path().stat().st_mode)
    except OSError:
        return None
