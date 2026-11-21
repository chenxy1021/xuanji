"""FastAPI 依赖：取当前用户 / 强制登录 / 强制管理员。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.core import accounts
from app.core.accounts import User
from app.core.errors import AppError


def client_ip(request: Request) -> str:
    """登录节流用的来源地址。本项目不做代理层，直接取 socket peer。"""
    return request.client.host if request.client else "unknown"


def session_token(request: Request) -> str | None:
    return request.cookies.get(accounts.SESSION_COOKIE)


def current_user(request: Request) -> User | None:
    """匿名也返回 None，不抛错。"""
    return accounts.user_for_session(session_token(request) or "")


def require_user(user: Annotated[User | None, Depends(current_user)]) -> User:
    if user is None:
        raise AppError("auth_required", "请先登录", 401)
    return user


def require_admin(user: Annotated[User, Depends(require_user)]) -> User:
    if not user.is_admin:
        raise AppError("admin_required", "需要管理员权限", 403)
    return user


CurrentUser = Annotated[User | None, Depends(current_user)]
RequiredUser = Annotated[User, Depends(require_user)]
AdminUser = Annotated[User, Depends(require_admin)]
