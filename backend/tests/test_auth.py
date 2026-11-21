"""账号体系：注册 / 登录 / 登出 / me、Cookie 属性、管理员判定、登录节流。"""

from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from app.core import accounts, db
from app.main import app

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"

PASSWORD = "alice-pass-123"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _register(client: TestClient, username: str = "alice", password: str = PASSWORD):
    return client.post(REGISTER, json={"username": username, "password": password})


def _cookie_attrs(res) -> list[str]:
    """取出 sm_session 那条 Set-Cookie 的属性（除 name=value 之外）。"""
    for header in res.headers.get_list("set-cookie"):
        if header.startswith(f"{accounts.SESSION_COOKIE}="):
            return [part.strip().lower() for part in header.split(";")[1:]]
    return []


def _rows(sql: str, params: tuple = ()) -> list:
    with db.session() as conn:
        return conn.execute(sql, params).fetchall()


def test_first_user_is_admin_and_gets_session_cookie(client) -> None:
    res = _register(client)
    assert res.status_code == 201
    user = res.json()["user"]
    assert user["username"] == "alice"
    assert user["is_admin"] is True
    assert user["id"]

    attrs = _cookie_attrs(res)
    assert "httponly" in attrs
    assert "samesite=lax" in attrs
    assert "path=/" in attrs
    assert "max-age=2592000" in attrs
    assert not any(attr.startswith("secure") for attr in attrs)

    # 注册即登录
    assert client.get(ME).json()["user"]["username"] == "alice"


def test_second_user_is_not_admin(client) -> None:
    assert _register(client, "alice").json()["user"]["is_admin"] is True
    res = _register(client, "bob")
    assert res.status_code == 201
    assert res.json()["user"]["is_admin"] is False


def test_admin_username_env_grants_admin(client, monkeypatch) -> None:
    assert _register(client, "alice").json()["user"]["is_admin"] is True
    monkeypatch.setenv("SM_ADMIN_USERNAME", "Boss")
    res = _register(client, "boss")
    assert res.status_code == 201
    assert res.json()["user"]["is_admin"] is True
    # 大小写不敏感，且不影响正常用户
    assert _register(client, "carol").json()["user"]["is_admin"] is False


def test_duplicate_username_is_conflict_case_insensitive(client) -> None:
    assert _register(client, "Alice").status_code == 201
    res = _register(client, "alice")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "username_taken"


@pytest.mark.parametrize(
    ("username", "password", "code"),
    [
        ("ab", PASSWORD, "invalid_username"),
        ("a" * 33, PASSWORD, "invalid_username"),
        ("bad name", PASSWORD, "invalid_username"),
        ("中文名字", PASSWORD, "invalid_username"),
        ("alice", "short", "weak_password"),
        ("alice", "x" * 129, "weak_password"),
    ],
)
def test_rejects_invalid_username_and_weak_password(client, username, password, code) -> None:
    res = _register(client, username, password)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == code


def test_login_and_me_cycle(client) -> None:
    assert _register(client, "alice").status_code == 201
    assert client.post(LOGOUT).status_code == 204
    assert client.get(ME).json()["user"] is None

    res = client.post(LOGIN, json={"username": "alice", "password": PASSWORD})
    assert res.status_code == 200
    assert res.json()["user"]["username"] == "alice"
    assert _cookie_attrs(res)
    assert client.get(ME).json()["user"]["username"] == "alice"


def test_me_is_public_and_returns_null_when_anonymous(client) -> None:
    res = client.get(ME)
    assert res.status_code == 200
    assert res.json() == {"user": None}


def test_wrong_password_and_unknown_user_look_identical(client) -> None:
    assert _register(client, "alice").status_code == 201
    wrong = client.post(LOGIN, json={"username": "alice", "password": "wrong-pass-1"})
    ghost = client.post(LOGIN, json={"username": "ghost", "password": "wrong-pass-1"})
    assert wrong.status_code == ghost.status_code == 401
    assert wrong.json() == ghost.json()
    assert wrong.json()["error"]["code"] == "invalid_credentials"


def test_logout_deletes_server_session(client) -> None:
    assert _register(client, "alice").status_code == 201
    token = client.cookies[accounts.SESSION_COOKIE]
    assert _rows("SELECT token_hash FROM sessions WHERE token_hash = ?", (hashlib.sha256(token.encode()).hexdigest(),))
    res = client.post(LOGOUT)
    assert res.status_code == 204
    assert client.get(ME).json()["user"] is None
    assert _rows("SELECT token_hash FROM sessions") == []


def test_session_token_is_stored_hashed(client) -> None:
    assert _register(client, "alice").status_code == 201
    token = client.cookies[accounts.SESSION_COOKIE]
    stored = [row["token_hash"] for row in _rows("SELECT token_hash FROM sessions")]
    assert token not in stored
    assert hashlib.sha256(token.encode()).hexdigest() in stored


def test_password_hash_format_and_verification(client) -> None:
    assert _register(client, "alice").status_code == 201
    digest = _rows("SELECT password_hash FROM users")[0]["password_hash"]
    scheme, n, r, p, salt_hex, hash_hex = digest.split("$")
    assert (scheme, n, r, p) == ("scrypt", "16384", "8", "1")
    assert len(bytes.fromhex(salt_hex)) == 16
    assert len(bytes.fromhex(hash_hex)) == 32
    assert PASSWORD not in digest
    assert accounts.verify_password(PASSWORD, digest) is True
    assert accounts.verify_password("wrong-pass-1", digest) is False
    assert accounts.verify_password(PASSWORD, "garbage") is False


def test_login_throttle_blocks_after_ten_failures(client) -> None:
    assert _register(client, "alice").status_code == 201
    for _ in range(10):
        assert client.post(LOGIN, json={"username": "alice", "password": "wrong-pass-1"}).status_code == 401

    blocked = client.post(LOGIN, json={"username": "alice", "password": "wrong-pass-1"})
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "too_many_attempts"
    # 正确密码在节流期内同样被挡，避免用来试探
    assert client.post(LOGIN, json={"username": "alice", "password": PASSWORD}).status_code == 429

    # 其它用户名不受影响
    accounts.throttle_clear(accounts.throttle_key("testclient", "alice"))
    assert client.post(LOGIN, json={"username": "alice", "password": PASSWORD}).status_code == 200


def test_successful_login_clears_throttle(client) -> None:
    assert _register(client, "alice").status_code == 201
    for _ in range(9):
        client.post(LOGIN, json={"username": "alice", "password": "wrong-pass-1"})
    assert client.post(LOGIN, json={"username": "alice", "password": PASSWORD}).status_code == 200
    for _ in range(9):
        assert client.post(LOGIN, json={"username": "alice", "password": "wrong-pass-1"}).status_code == 401


def test_cookie_secure_flag_follows_env(client, monkeypatch) -> None:
    monkeypatch.setenv("SM_COOKIE_SECURE", "1")
    res = _register(client, "alice")
    assert res.status_code == 201
    assert "secure" in _cookie_attrs(res)


def test_register_response_has_no_secret_fields(client) -> None:
    body = _register(client).json()
    assert set(body) == {"user"}
    assert "password" not in str(body).lower()
    assert "hash" not in str(body).lower()
