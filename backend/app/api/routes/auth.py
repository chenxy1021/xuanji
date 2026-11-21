"""账号：注册 / 登录 / 登出 / 当前用户。

产品规则（与前端约定一致）：
- 用户名 + 密码开放注册；第一个注册的用户是管理员。
- 环境变量 `SM_ADMIN_USERNAME` 指定的用户名注册时也是管理员。
- Cookie 名 `sm_session`，HttpOnly + SameSite=Lax + Path=/ + 30 天；
  `Secure` 由 `SM_COOKIE_SECURE=1` 打开（默认关，适配本机 http）。
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, client_ip
from app.core import accounts
from app.core.errors import AppError

router = APIRouter(tags=["auth"])


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: str
    username: str
    is_admin: bool


class MeResponse(BaseModel):
    user: UserOut | None = None


def _cookie_secure() -> bool:
    return (os.getenv("SM_COOKIE_SECURE") or "").strip().lower() in {"1", "true", "yes", "on"}


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=accounts.SESSION_COOKIE,
        value=token,
        max_age=accounts.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        path="/",
        secure=_cookie_secure(),
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=accounts.SESSION_COOKIE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
    )


def _validated(payload: Credentials) -> tuple[str, str]:
    username = payload.username.strip()
    message = accounts.username_error(username)
    if message:
        raise AppError("invalid_username", message, 422)
    message = accounts.password_error(payload.password)
    if message:
        raise AppError("weak_password", message, 422)
    return username, payload.password


@router.post("/auth/register", status_code=201, summary="注册（首个用户为管理员）")
def register(payload: Credentials, response: Response) -> dict[str, Any]:
    username, password = _validated(payload)
    user = accounts.create_user(username, password)
    token = accounts.start_session(user.id)
    _set_session_cookie(response, token)
    return {"user": user.public()}


@router.post("/auth/login", summary="登录")
def login(payload: Credentials, request: Request, response: Response) -> dict[str, Any]:
    username = payload.username.strip()
    key = accounts.throttle_key(client_ip(request), username)
    if accounts.throttle_blocked(key):
        raise AppError("too_many_attempts", "登录尝试过于频繁，请稍后再试", 429)
    user = accounts.authenticate(username, payload.password)
    if user is None:
        accounts.throttle_fail(key)
        raise AppError("invalid_credentials", "用户名或密码不正确", 401)
    accounts.throttle_clear(key)
    token = accounts.start_session(user.id)
    _set_session_cookie(response, token)
    return {"user": user.public()}


@router.post("/auth/logout", status_code=204, summary="登出")
def logout(request: Request, response: Response) -> Response:
    accounts.end_session(request.cookies.get(accounts.SESSION_COOKIE) or "")
    _clear_session_cookie(response)
    response.status_code = 204
    return response


@router.get("/auth/me", response_model=MeResponse, summary="当前用户（匿名也 200）")
def me(user: CurrentUser) -> dict[str, Any]:
    return {"user": user.public() if user else None}
