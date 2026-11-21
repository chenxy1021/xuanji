"""运行能力探测接口：前端用它在 AI 面板提前提示未配置密钥。"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _public(configured: bool) -> dict[str, Any]:
    return {
        "configured": configured,
        "base_url": "https://api.example.com/v1",
        "model": "test-model",
        "source": "env" if configured else "default",
        "key_hint": "••••1234" if configured else "",
    }


def test_meta_reports_llm_off(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.meta.llm_store.public", lambda: _public(False))
    res = client.get("/api/v1/meta")
    assert res.status_code == 200
    assert res.json() == {
        "llm_configured": False,
        "llm_base_url": "https://api.example.com/v1",
        "llm_model": "test-model",
        "llm_source": "default",
        "llm_key_hint": "",
    }


def test_meta_reports_llm_on(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.meta.llm_store.public", lambda: _public(True))
    res = client.get("/api/v1/meta")
    assert res.status_code == 200
    body = res.json()
    assert body["llm_configured"] is True
    assert body["llm_key_hint"] == "••••1234"
    assert res.headers["cache-control"] == "no-store"
