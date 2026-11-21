"""排盘记录与 AI 解读的读写（按 user_id 隔离）。

- 记录本体存 `records`，可变长度的业务字段（engine_version / input / chart / text /
  warnings）序列化进 `payload`，这样字段增减不用改表。
- 所有查询都带 `user_id` 条件：跨用户访问一律当作不存在（404），不泄露存在性。
- 每用户最多 50 条，插入后按 `created_at` 淘汰更旧的。
- 体积上限：text 20 万字、payload 序列化后 500KB，超出返回 413。
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.core import accounts, db
from app.core.errors import AppError

MAX_RECORDS = 50
TEXT_MAX_CHARS = 200_000
PAYLOAD_MAX_BYTES = 500_000


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _check_size(text: str, payload: dict[str, Any]) -> None:
    if len(text) > TEXT_MAX_CHARS:
        raise AppError("text_too_large", f"解读文本超过上限（{TEXT_MAX_CHARS} 字）", 413)
    size = len(_dump(payload).encode("utf-8"))
    if size > PAYLOAD_MAX_BYTES:
        raise AppError("payload_too_large", "记录内容超过上限（500KB）", 413)


def _row_to_record(row: Any) -> dict[str, Any]:
    payload = json.loads(row["payload"])
    return {
        "id": row["id"],
        "createdAt": row["created_at"],
        "title": row["title"],
        "system": row["system"],
        "engine_version": payload.get("engine_version", ""),
        "input": payload.get("input") or {},
        "chart": payload.get("chart") or {},
        "text": payload.get("text") or "",
        "warnings": payload.get("warnings") or [],
    }


def create_record(
    user_id: str,
    *,
    system: str,
    title: str,
    engine_version: str,
    input: dict[str, Any],
    chart: dict[str, Any],
    text: str,
    warnings: list[str],
) -> dict[str, Any]:
    payload = {
        "engine_version": engine_version,
        "input": input,
        "chart": chart,
        "text": text,
        "warnings": warnings,
    }
    _check_size(text, payload)
    record_id = uuid.uuid4().hex
    created = accounts.now_ms()
    with db.session() as conn:
        conn.execute(
            "INSERT INTO records(id, user_id, system, title, payload, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (record_id, user_id, system, title, _dump(payload), created),
        )
        conn.execute(
            "DELETE FROM records WHERE user_id = ? AND id NOT IN ("
            " SELECT id FROM records WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?"
            ")",
            (user_id, user_id, MAX_RECORDS),
        )
    return {
        "id": record_id,
        "createdAt": created,
        "title": title,
        "system": system,
        "engine_version": engine_version,
        "input": input,
        "chart": chart,
        "text": text,
        "warnings": warnings,
    }


def list_records(user_id: str, limit: int = MAX_RECORDS) -> list[dict[str, Any]]:
    with db.session() as conn:
        rows = conn.execute(
            "SELECT * FROM records WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def get_record(user_id: str, record_id: str) -> dict[str, Any] | None:
    with db.session() as conn:
        row = conn.execute(
            "SELECT * FROM records WHERE id = ? AND user_id = ?", (record_id, user_id)
        ).fetchone()
    return _row_to_record(row) if row else None


def record_exists(user_id: str, record_id: str) -> bool:
    with db.session() as conn:
        row = conn.execute(
            "SELECT 1 FROM records WHERE id = ? AND user_id = ?", (record_id, user_id)
        ).fetchone()
    return row is not None


def delete_record(user_id: str, record_id: str) -> bool:
    with db.session() as conn:
        cursor = conn.execute(
            "DELETE FROM records WHERE id = ? AND user_id = ?", (record_id, user_id)
        )
    return cursor.rowcount > 0


def clear_records(user_id: str) -> int:
    with db.session() as conn:
        cursor = conn.execute("DELETE FROM records WHERE user_id = ?", (user_id,))
    return cursor.rowcount


# --- AI 解读 ------------------------------------------------------------


def _row_to_reading(row: Any) -> dict[str, Any]:
    try:
        focus = json.loads(row["focus"] or "[]")
    except ValueError:
        focus = []
    if isinstance(focus, str):
        focus = [focus]
    return {
        "text": row["text"],
        "focus": focus if isinstance(focus, list) else [],
        "style": row["style"],
        "question": row["question"],
        "system": row["system"],
        "updatedAt": row["updated_at"],
    }


def get_reading(user_id: str, record_id: str) -> dict[str, Any] | None:
    with db.session() as conn:
        row = conn.execute(
            "SELECT * FROM readings WHERE record_id = ? AND user_id = ?", (record_id, user_id)
        ).fetchone()
    return _row_to_reading(row) if row else None


def put_reading(
    user_id: str,
    record_id: str,
    *,
    text: str,
    focus: list[str] | str | None,
    style: str | None,
    question: str | None,
    system: str | None,
) -> dict[str, Any]:
    if len(text) > TEXT_MAX_CHARS:
        raise AppError("text_too_large", f"解读文本超过上限（{TEXT_MAX_CHARS} 字）", 413)
    if isinstance(focus, str):
        focus_list = [focus] if focus.strip() else []
    else:
        focus_list = [str(item) for item in (focus or []) if str(item).strip()]
    if len(focus_list) > 20:
        raise AppError("too_many_focus", "解读方向最多 20 个", 422)
    updated = accounts.now_ms()
    with db.session() as conn:
        conn.execute(
            "INSERT INTO readings(record_id, user_id, text, focus, style, question, system,"
            " updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(record_id) DO UPDATE SET text = excluded.text, focus = excluded.focus,"
            " style = excluded.style, question = excluded.question, system = excluded.system,"
            " updated_at = excluded.updated_at, user_id = excluded.user_id",
            (
                record_id,
                user_id,
                text,
                _dump(focus_list),
                style,
                question,
                system,
                updated,
            ),
        )
    return {
        "text": text,
        "focus": focus_list,
        "style": style,
        "question": question,
        "system": system,
        "updatedAt": updated,
    }


def delete_reading(user_id: str, record_id: str) -> bool:
    with db.session() as conn:
        cursor = conn.execute(
            "DELETE FROM readings WHERE record_id = ? AND user_id = ?", (record_id, user_id)
        )
    return cursor.rowcount > 0
