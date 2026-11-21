"""测试隔离：不要读写开发者本机保存的模型配置与账号数据库。"""

from __future__ import annotations

import pytest

from app.core import accounts


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SM_LLM_CONFIG_PATH", str(tmp_path / "llm.json"))
    monkeypatch.setenv("SM_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.delenv("SM_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("SM_COOKIE_SECURE", raising=False)
    accounts.reset_throttle()
    yield
    accounts.reset_throttle()
