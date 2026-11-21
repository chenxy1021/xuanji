"""账号、会话与登录节流：全部用标准库实现，不引第三方依赖。

安全要点：
- 密码用 `hashlib.scrypt`（n=16384, r=8, p=1，16 字节随机盐），
  存成 `scrypt$n$r$p$salt_hex$hash_hex`，校验用 `hmac.compare_digest`。
- 会话只存 token 的 SHA-256，库里没有明文 token；有效期 30 天。
- 登录失败做 IP + 用户名维度节流（5 分钟 10 次），内存字典 + 锁，
  进程重启清零；多进程部署时每个进程独立计数（够用即可）。
- 登录失败一律「用户名或密码不正确」，不区分用户是否存在；
  用户不存在时也跑一次 scrypt，避免响应时间泄露。
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from functools import lru_cache

from app.core import db
from app.core.errors import AppError

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
USERNAME_MIN, USERNAME_MAX = 3, 32
PASSWORD_MIN, PASSWORD_MAX = 8, 128

_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32
_SALT_BYTES = 16

SESSION_COOKIE = "sm_session"
SESSION_TTL_SECONDS = 30 * 24 * 3600

_THROTTLE_WINDOW = 300.0
_THROTTLE_MAX = 10
_FAIL_LOCK = threading.Lock()
_FAILURES: dict[tuple[str, str], list[float]] = {}


@dataclass(frozen=True)
class User:
    id: str
    username: str
    is_admin: bool

    def public(self) -> dict[str, object]:
        return {"id": self.id, "username": self.username, "is_admin": self.is_admin}


def now_ms() -> int:
    return int(time.time() * 1000)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --- 密码 ---------------------------------------------------------------


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, hash_hex = (stored or "").split("$")
        if scheme != "scrypt":
            return False
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(hash_hex) // 2,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived.hex(), hash_hex)


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    """用户不存在时也消耗等量算力，避免用耗时判断账号是否存在。"""
    return hash_password(secrets.token_urlsafe(16))


# --- 用户名 / 密码校验 ---------------------------------------------------


def username_error(username: str) -> str | None:
    if not USERNAME_RE.fullmatch(username or ""):
        return f"用户名需 {USERNAME_MIN}-{USERNAME_MAX} 位，仅限字母、数字、下划线、点、短横线"
    return None


def password_error(password: str) -> str | None:
    if not isinstance(password, str) or not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return f"密码需 {PASSWORD_MIN}-{PASSWORD_MAX} 个字符"
    return None


def admin_username() -> str:
    """环境变量里指定的管理员用户名（大小写不敏感），空串视为未设置。"""
    return (os.getenv("SM_ADMIN_USERNAME") or "").strip()


def _is_admin_name(username: str) -> bool:
    expected = admin_username()
    return bool(expected) and expected.lower() == username.lower()


# --- 用户 ---------------------------------------------------------------


def create_user(username: str, password: str) -> User:
    """建号：库里的第一个用户是管理员；`SM_ADMIN_USERNAME` 指定的用户名也是管理员。"""
    digest = hash_password(password)
    user_id = uuid.uuid4().hex
    created = now_ms()
    with db.session() as conn:
        # 串行化「第一个用户」的判定，避免并发注册都拿到管理员
        conn.execute("BEGIN IMMEDIATE")
        total = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        is_admin = 1 if total == 0 or _is_admin_name(username) else 0
        try:
            conn.execute(
                "INSERT INTO users(id, username, password_hash, is_admin, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (user_id, username, digest, is_admin, created),
            )
        except sqlite3.IntegrityError as exc:
            raise AppError("username_taken", "该用户名已被占用", 409) from exc
    return User(id=user_id, username=username, is_admin=bool(is_admin))


def authenticate(username: str, password: str) -> User | None:
    with db.session() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, is_admin FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        verify_password(password, _dummy_hash())
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return User(id=row["id"], username=row["username"], is_admin=bool(row["is_admin"]))


def user_for_session(token: str) -> User | None:
    if not token:
        return None
    token_hash = _token_hash(token)
    with db.session() as conn:
        row = conn.execute(
            "SELECT u.id, u.username, u.is_admin, s.expires_at"
            " FROM sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token_hash = ?",
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] <= now_ms():
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            return None
    return User(id=row["id"], username=row["username"], is_admin=bool(row["is_admin"]))


# --- 会话 ---------------------------------------------------------------


def start_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    created = now_ms()
    with db.session() as conn:
        conn.execute(
            "INSERT INTO sessions(token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_token_hash(token), user_id, created, created + SESSION_TTL_SECONDS * 1000),
        )
        # 顺手清理过期会话，省得单独跑定时任务
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (created,))
    return token


def end_session(token: str) -> None:
    if not token:
        return
    with db.session() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


# --- 登录节流 -----------------------------------------------------------


def throttle_key(ip: str, username: str) -> tuple[str, str]:
    return (ip or "unknown", (username or "").lower())


def _recent(key: tuple[str, str], now: float) -> list[float]:
    stamps = [t for t in _FAILURES.get(key, []) if now - t < _THROTTLE_WINDOW]
    if stamps:
        _FAILURES[key] = stamps
    else:
        _FAILURES.pop(key, None)
    return stamps


def throttle_blocked(key: tuple[str, str]) -> bool:
    with _FAIL_LOCK:
        return len(_recent(key, time.monotonic())) >= _THROTTLE_MAX


def throttle_fail(key: tuple[str, str]) -> None:
    with _FAIL_LOCK:
        now = time.monotonic()
        stamps = _recent(key, now)
        stamps.append(now)
        _FAILURES[key] = stamps


def throttle_clear(key: tuple[str, str]) -> None:
    with _FAIL_LOCK:
        _FAILURES.pop(key, None)


def reset_throttle() -> None:
    with _FAIL_LOCK:
        _FAILURES.clear()
