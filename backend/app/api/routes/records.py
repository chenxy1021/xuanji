"""排盘记录与 AI 解读：全部按登录用户隔离，未登录一律 401。

契约（前端按此实现）：
- `GET    /records`                    → HistoryRecord[]（createdAt 倒序，最多 50）
- `POST   /records`                    → 201 HistoryRecord（服务端生成 id / createdAt）
- `GET    /records/{id}`               → HistoryRecord
- `DELETE /records/{id}`               → 204
- `DELETE /records`                    → 204 清空本人记录
- `GET    /records/{id}/reading`       → Readout | null
- `PUT    /records/{id}/reading`       → Readout
- `DELETE /records/{id}/reading`       → 204
跨用户访问统一 404，不区分「不存在」与「不是你的」。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from app.api.deps import RequiredUser
from app.core import records as store
from app.core.errors import AppError

router = APIRouter(tags=["records"])


class RecordIn(BaseModel):
    system: str = Field(min_length=1, max_length=40)
    title: str = Field(default="", max_length=200)
    engine_version: str = Field(default="", max_length=40)
    input: dict[str, Any] = Field(default_factory=dict)
    chart: dict[str, Any] = Field(default_factory=dict)
    text: str = ""
    warnings: list[str] = Field(default_factory=list)


class HistoryRecord(BaseModel):
    id: str
    createdAt: int
    title: str
    system: str
    engine_version: str
    input: dict[str, Any]
    chart: dict[str, Any]
    text: str
    warnings: list[str]


class ReadingIn(BaseModel):
    text: str = ""
    focus: list[str] | str | None = None
    style: str | None = Field(default=None, max_length=20)
    question: str | None = Field(default=None, max_length=500)
    system: str | None = Field(default=None, max_length=40)


class ReadingOut(BaseModel):
    text: str
    focus: list[str] = Field(default_factory=list)
    style: str | None = None
    question: str | None = None
    system: str | None = None
    updatedAt: int


def _require_record(user_id: str, record_id: str) -> None:
    if not store.record_exists(user_id, record_id):
        raise AppError("record_not_found", "记录不存在", 404)


@router.get("/records", response_model=list[HistoryRecord], summary="我的记录")
def list_records(user: RequiredUser) -> list[dict[str, Any]]:
    return store.list_records(user.id)


@router.post("/records", response_model=HistoryRecord, status_code=201, summary="保存一条记录")
def create_record(payload: RecordIn, user: RequiredUser) -> dict[str, Any]:
    return store.create_record(
        user.id,
        system=payload.system,
        title=payload.title,
        engine_version=payload.engine_version,
        input=payload.input,
        chart=payload.chart,
        text=payload.text,
        warnings=payload.warnings,
    )


@router.delete("/records", status_code=204, summary="清空我的记录")
def clear_records(user: RequiredUser) -> Response:
    store.clear_records(user.id)
    return Response(status_code=204)


@router.get("/records/{record_id}", response_model=HistoryRecord, summary="单条记录")
def get_record(record_id: str, user: RequiredUser) -> dict[str, Any]:
    record = store.get_record(user.id, record_id)
    if record is None:
        raise AppError("record_not_found", "记录不存在", 404)
    return record


@router.delete("/records/{record_id}", status_code=204, summary="删除单条记录")
def delete_record(record_id: str, user: RequiredUser) -> Response:
    if not store.delete_record(user.id, record_id):
        raise AppError("record_not_found", "记录不存在", 404)
    return Response(status_code=204)


@router.get(
    "/records/{record_id}/reading",
    response_model=ReadingOut | None,
    summary="该记录的解读存档（没有再返回 null）",
)
def get_reading(record_id: str, user: RequiredUser) -> dict[str, Any] | None:
    _require_record(user.id, record_id)
    return store.get_reading(user.id, record_id)


@router.put(
    "/records/{record_id}/reading", response_model=ReadingOut, summary="写入 / 覆盖解读存档"
)
def put_reading(record_id: str, payload: ReadingIn, user: RequiredUser) -> dict[str, Any]:
    _require_record(user.id, record_id)
    return store.put_reading(
        user.id,
        record_id,
        text=payload.text,
        focus=payload.focus,
        style=payload.style,
        question=payload.question,
        system=payload.system,
    )


@router.delete("/records/{record_id}/reading", status_code=204, summary="删除解读存档")
def delete_reading(record_id: str, user: RequiredUser) -> Response:
    _require_record(user.id, record_id)
    if not store.delete_reading(user.id, record_id):
        raise AppError("reading_not_found", "该记录还没有解读存档", 404)
    return Response(status_code=204)
