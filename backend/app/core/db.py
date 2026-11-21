"""SQLite 存储底座：连接、建表、权限收紧。

设计取舍：
- 默认库文件 `backend/.local/app.db`，可用 `SM_DB_PATH` 覆盖（测试 / 容器）。
  每次调用都重新读环境变量，方便测试按用例切换库。
- 每个请求开一条独立连接（WAL + `foreign_keys=ON` + busy_timeout），
  不共享全局连接，避免多线程下的 `sqlite3` 线程限制与锁竞争。
- 本模块只负责连接与 schema；用户、会话见 `accounts`，记录与解读见 `records`。
- 不做迁移框架：`CREATE TABLE IF NOT EXISTS` 幂等，加字段时手工补 `ALTER`。
"""

from __future__ import annotations

import os
import sqlite3
import stat
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / ".local" / "app.db"
_INIT_LOCK = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    created_at    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS records (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    system     TEXT NOT NULL,
    title      TEXT NOT NULL DEFAULT '',
    payload    TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_records_user ON records(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS readings (
    record_id  TEXT PRIMARY KEY REFERENCES records(id) ON DELETE CASCADE,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text       TEXT NOT NULL DEFAULT '',
    focus      TEXT NOT NULL DEFAULT '[]',
    style      TEXT,
    question   TEXT,
    system     TEXT,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_readings_user ON readings(user_id);
"""


def db_path() -> Path:
    """库文件位置：`SM_DB_PATH` 优先，否则后端目录下的 `.local/app.db`。"""
    override = os.getenv("SM_DB_PATH")
    return Path(override) if override else _DEFAULT_PATH


def _chmod_if_needed(path: Path, mode: int) -> None:
    """只在权限不符时才 chmod，避免每次开连接都白跑系统调用。"""
    try:
        current = stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return
    if current != mode:
        path.chmod(mode)


def _harden(target: Path) -> None:
    """目录 0700、库文件（含 -wal/-shm）0600；不支持 chmod 的文件系统直接跳过。

    每次连接都会调用：库文件可能由外部工具或备份恢复产生，
    首次连接前就存在且权限放宽（如 0644），此时也必须收紧。
    新建的 `-wal`/`-shm` 会在下一次连接时被兜住。
    """
    try:
        _chmod_if_needed(target.parent, 0o700)
        for path in target.parent.glob(f"{target.name}*"):
            _chmod_if_needed(path, 0o600)
    except OSError:  # pragma: no cover - 取决于文件系统
        pass


def connect() -> sqlite3.Connection:
    """打开一条连接并确保 schema 就绪。调用方负责 close。"""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    with _INIT_LOCK:
        conn.executescript(_SCHEMA)
        _harden(path)
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    """自动提交 / 回滚并关闭连接。"""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
