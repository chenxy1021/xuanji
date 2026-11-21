"""设置页的模型配置：写入、掩码、校验、回落。"""

from __future__ import annotations

import os
import stat
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core import llm_store
from app.main import app

client = TestClient(app)

ADMIN = {"username": "settings_admin", "password": "admin-pass-123"}


@pytest.fixture(autouse=True)
def _admin_session(_isolate_state):
    """设置接口改为仅管理员可用：每个用例先注册管理员，复用其 Cookie。"""
    client.cookies.clear()
    res = client.post("/api/v1/auth/register", json=ADMIN)
    assert res.status_code == 201
    assert res.json()["user"]["is_admin"] is True
    yield
    client.cookies.clear()


def _base(**overrides):
    values = {
        "llm_api_key": "",
        "llm_base_url": "https://api.deepseek.com",
        "llm_model": "deepseek-chat",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_defaults_when_nothing_configured(monkeypatch) -> None:
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base())
    res = client.get("/api/v1/settings/llm")
    assert res.status_code == 200
    body = res.json()
    assert body == {
        "configured": False,
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "source": "default",
        "key_hint": "",
    }
    assert res.headers["cache-control"] == "no-store"


def test_save_masks_key_and_never_returns_it(monkeypatch) -> None:
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base())
    res = client.put(
        "/api/v1/settings/llm",
        json={
            "base_url": "https://api.example.com/v1/",
            "model": "example-model",
            "api_key": "sk-test-abcd1234",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["configured"] is True
    assert body["base_url"] == "https://api.example.com/v1"
    assert body["model"] == "example-model"
    assert body["key_hint"] == "••••1234"
    assert body["source"] == "runtime"
    assert "api_key" not in body

    meta = client.get("/api/v1/meta").json()
    assert meta["llm_configured"] is True

    saved = llm_store.config_path()
    assert "sk-test-abcd1234" in saved.read_text("utf-8")
    if os.name == "posix":
        assert stat.S_IMODE(saved.stat().st_mode) == 0o600


def test_blank_key_keeps_existing_key(monkeypatch) -> None:
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base())
    client.put("/api/v1/settings/llm", json={"api_key": "sk-keep-9999"})
    res = client.put("/api/v1/settings/llm", json={"api_key": "", "model": "other-model"})
    body = res.json()
    assert body["configured"] is True
    assert body["key_hint"] == "••••9999"
    assert body["model"] == "other-model"


def test_short_key_is_fully_masked(monkeypatch) -> None:
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base())
    body = client.put("/api/v1/settings/llm", json={"api_key": "sk-1234"}).json()
    assert body["configured"] is True
    assert body["key_hint"] == "••••"


def test_clear_key_falls_back_to_env(monkeypatch) -> None:
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base(llm_api_key="sk-env-key-0000"))
    client.put("/api/v1/settings/llm", json={"api_key": "sk-runtime-1111"})
    res = client.put("/api/v1/settings/llm", json={"clear_key": True})
    body = res.json()
    assert body["configured"] is True
    assert body["source"] == "env"
    assert body["key_hint"] == "••••0000"


def test_delete_resets_runtime(monkeypatch) -> None:
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base())
    client.put("/api/v1/settings/llm", json={"api_key": "sk-delete-2222"})
    res = client.delete("/api/v1/settings/llm")
    assert res.status_code == 200
    assert res.json()["configured"] is False
    assert not llm_store.config_path().exists()


def test_rejects_bad_url_and_model(monkeypatch) -> None:
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base())
    assert client.put("/api/v1/settings/llm", json={"base_url": "ftp://x"}).status_code == 422
    assert client.put("/api/v1/settings/llm", json={"base_url": "not a url"}).status_code == 422
    assert client.put("/api/v1/settings/llm", json={"model": "bad model"}).status_code == 422
    assert client.put("/api/v1/settings/llm", json={"api_key": "bad\nkey"}).status_code == 422


def test_settings_require_admin(monkeypatch) -> None:
    """未登录 401、已登录非管理员 403；/meta 仍对匿名开放。"""
    monkeypatch.setattr(llm_store, "get_settings", lambda: _base())
    anonymous = TestClient(app)
    assert anonymous.get("/api/v1/settings/llm").status_code == 401
    assert anonymous.get("/api/v1/meta").status_code == 200
    assert anonymous.get("/api/v1/meta").json()["llm_configured"] is False

    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/register",
        json={"username": "settings_viewer", "password": "viewer-pass-1"},
    )
    assert res.status_code == 201
    assert res.json()["user"]["is_admin"] is False

    assert client.get("/api/v1/settings/llm").status_code == 403
    assert client.put("/api/v1/settings/llm", json={"model": "x-model"}).status_code == 403
    assert client.delete("/api/v1/settings/llm").status_code == 403
    assert not llm_store.config_path().exists()
