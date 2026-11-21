"""存储底座：库路径可覆盖、文件权限收紧、WAL/外键生效、级联删除。"""

from __future__ import annotations

import os
import stat

import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.main import app


def test_db_path_follows_env() -> None:
    path = db.db_path()
    assert path.name == "app.db"
    assert "app.db" in os.getenv("SM_DB_PATH", "")
    with db.session() as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert {"users", "sessions", "records", "readings"} <= tables


def test_db_file_permissions_are_tight() -> None:
    client = TestClient(app)
    assert client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "alice-pass-123"},
    ).status_code == 201

    path = db.db_path()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


@pytest.mark.skipif(os.name != "posix", reason="权限位是 POSIX 语义")
def test_existing_db_file_is_tightened_on_connect(tmp_path, monkeypatch) -> None:
    """库文件在首次连接前就存在（外部工具建的空文件 / 备份恢复）时也要收紧权限。"""
    target = tmp_path / "data" / "app.db"
    target.parent.mkdir(parents=True)
    target.parent.chmod(0o755)
    target.touch()
    target.chmod(0o644)
    monkeypatch.setenv("SM_DB_PATH", str(target))

    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] == 0
    finally:
        conn.close()

    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700


def test_connect_is_idempotent_on_wide_permissions(tmp_path, monkeypatch) -> None:
    """重复连接不会因为权限已正确而报错或改坏文件。"""
    target = tmp_path / "twice" / "app.db"
    monkeypatch.setenv("SM_DB_PATH", str(target))
    for _ in range(3):
        with db.session() as conn:
            assert conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] == 0
    if os.name == "posix":
        assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_deleting_user_cascades_records_and_readings() -> None:
    client = TestClient(app)
    user = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "alice-pass-123"},
    ).json()["user"]
    record = client.post(
        "/api/v1/records",
        json={
            "system": "bazi",
            "title": "示例",
            "engine_version": "0.1.0",
            "input": {},
            "chart": {},
            "text": "正文",
            "warnings": [],
        },
    ).json()
    client.put(f"/api/v1/records/{record['id']}/reading", json={"text": "解读"})

    with db.session() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    with db.session() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM records").fetchone()["n"] == 0
        assert conn.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"] == 0
        assert conn.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()["n"] == 0
