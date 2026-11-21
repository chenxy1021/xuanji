"""领域模块共用的辅助函数。"""

from __future__ import annotations

from app.core.errors import AppError


def not_ready(system: str, name: str) -> None:
    """未实现体系统一抛出 501。"""
    raise AppError("system_not_ready", f"「{name}」排盘正在开发中", 501)
