"""浏览器自带的模型配置：/interpret 可以覆盖本站默认，但要做同样校验。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi.testclient import TestClient

from app.core import llm_store
from app.main import app

client = TestClient(app)

CHART = {"system": "bazi", "chart": {}, "text": "四柱：甲戌 甲戌 庚辰 庚辰"}


def _capture(monkeypatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    async def fake_stream(
        messages: list[dict[str, str]],
        cfg: llm_store.LlmConfig | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        captured["cfg"] = cfg
        captured["messages"] = messages
        yield "解读"

    monkeypatch.setattr("app.api.routes.interpret.llm.stream_chat", fake_stream)
    return captured


def test_interpret_uses_browser_llm(monkeypatch) -> None:
    captured = _capture(monkeypatch)
    res = client.post(
        "/api/v1/interpret",
        json={
            **CHART,
            "llm": {
                "base_url": "http://127.0.0.1:3425/v1/",
                "model": "workbuddy/deepseek-v4.1-flash",
                "api_key": "magpie-local",
            },
        },
    )
    assert res.status_code == 200
    assert "解读" in res.text
    assert "event: done" in res.text
    cfg = captured["cfg"]
    assert cfg is not None
    assert cfg.base_url == "http://127.0.0.1:3425/v1"
    assert cfg.model == "workbuddy/deepseek-v4.1-flash"
    assert cfg.api_key == "magpie-local"
    assert cfg.source == "client"


def test_interpret_without_browser_llm_uses_server_default(monkeypatch) -> None:
    captured = _capture(monkeypatch)
    res = client.post("/api/v1/interpret", json=CHART)
    assert res.status_code == 200
    assert captured["cfg"] is None


def test_interpret_rejects_bad_browser_llm() -> None:
    for llm in (
        {"base_url": "ftp://example.com", "model": "m", "api_key": "k"},
        {"base_url": "https://example.com/v1", "model": "bad model", "api_key": "k"},
        {"base_url": "https://example.com/v1", "model": "m", "api_key": "bad\nkey"},
    ):
        res = client.post("/api/v1/interpret", json={**CHART, "llm": llm})
        assert res.status_code == 422, llm
