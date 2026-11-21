"""记录与解读：CRUD、未登录 401、A/B 隔离、50 条上限、超大内容拒绝。"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.core import accounts
from app.main import app

RECORDS = "/api/v1/records"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def other() -> TestClient:
    return TestClient(app)


def _signup(client: TestClient, username: str = "alice", password: str = "alice-pass-123") -> dict:
    res = client.post("/api/v1/auth/register", json={"username": username, "password": password})
    assert res.status_code == 201
    return res.json()["user"]


def _payload(**overrides):
    body = {
        "system": "bazi",
        "title": "示例 · 1990-01-01",
        "engine_version": "0.1.0",
        "input": {"birth": {"year": 1990, "month": 1, "day": 1}, "options": {}},
        "chart": {"pillars": ["甲子", "丙寅", "戊辰", "庚午"]},
        "text": "# 命盘\n\n四柱：甲子 丙寅 戊辰 庚午",
        "warnings": ["已按真太阳时校正"],
    }
    body.update(overrides)
    return body


def _create(client: TestClient, **overrides) -> dict:
    res = client.post(RECORDS, json=_payload(**overrides))
    assert res.status_code == 201, res.text
    return res.json()


def test_anonymous_gets_401_everywhere(client) -> None:
    for res in (
        client.get(RECORDS),
        client.post(RECORDS, json=_payload()),
        client.get(f"{RECORDS}/whatever"),
        client.delete(f"{RECORDS}/whatever"),
        client.delete(RECORDS),
        client.get(f"{RECORDS}/whatever/reading"),
        client.put(f"{RECORDS}/whatever/reading", json={"text": "x"}),
        client.delete(f"{RECORDS}/whatever/reading"),
    ):
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "auth_required"


def test_create_generates_server_side_id_and_timestamp(client) -> None:
    _signup(client)
    res = client.post(RECORDS, json=_payload(id="forged-id", createdAt=1, user_id="someone"))
    assert res.status_code == 201
    record = res.json()
    assert record["id"] != "forged-id"
    assert record["createdAt"] > 1_600_000_000_000
    assert set(record) == {
        "id",
        "createdAt",
        "title",
        "system",
        "engine_version",
        "input",
        "chart",
        "text",
        "warnings",
    }


def test_list_returns_newest_first(client) -> None:
    _signup(client)
    first = _create(client, title="第一条")
    second = _create(client, title="第二条")
    rows = client.get(RECORDS).json()
    assert [row["title"] for row in rows] == ["第二条", "第一条"]
    assert {row["id"] for row in rows} == {first["id"], second["id"]}


def test_get_round_trips_payload(client) -> None:
    _signup(client)
    created = _create(client)
    fetched = client.get(f"{RECORDS}/{created['id']}").json()
    assert fetched == created
    assert fetched["chart"] == _payload()["chart"]
    assert fetched["input"] == _payload()["input"]
    assert fetched["warnings"] == ["已按真太阳时校正"]


def test_records_are_isolated_between_users(client, other) -> None:
    _signup(client, "alice")
    _signup(other, "bob")
    mine = _create(client)

    assert client.get(RECORDS).json()[0]["id"] == mine["id"]
    assert other.get(RECORDS).json() == []
    assert other.get(f"{RECORDS}/{mine['id']}").status_code == 404
    assert other.delete(f"{RECORDS}/{mine['id']}").status_code == 404
    assert other.get(f"{RECORDS}/{mine['id']}/reading").status_code == 404
    assert other.put(f"{RECORDS}/{mine['id']}/reading", json={"text": "x"}).status_code == 404
    # 仍然存在，没有被别人删掉
    assert client.get(f"{RECORDS}/{mine['id']}").status_code == 200


def test_delete_record(client) -> None:
    _signup(client)
    created = _create(client)
    assert client.delete(f"{RECORDS}/{created['id']}").status_code == 204
    assert client.get(f"{RECORDS}/{created['id']}").status_code == 404
    assert client.delete(f"{RECORDS}/{created['id']}").status_code == 404
    assert client.get(RECORDS).json() == []


def test_clear_all_records(client) -> None:
    _signup(client)
    _create(client)
    _create(client)
    assert client.delete(RECORDS).status_code == 204
    assert client.get(RECORDS).json() == []


def test_record_cap_is_fifty(client, monkeypatch) -> None:
    clock = itertools.count(1_700_000_000_000, 1000)
    monkeypatch.setattr(accounts, "now_ms", lambda: next(clock))
    _signup(client)
    ids = [_create(client, title=f"第 {index} 条")["id"] for index in range(60)]

    rows = client.get(RECORDS).json()
    assert len(rows) == 50
    kept = {row["id"] for row in rows}
    assert kept == set(ids[-50:])
    assert client.get(f"{RECORDS}/{ids[0]}").status_code == 404


def test_rejects_oversized_content(client) -> None:
    _signup(client)
    too_long_text = client.post(RECORDS, json=_payload(text="字" * 200_001))
    assert too_long_text.status_code == 413
    assert too_long_text.json()["error"]["code"] == "text_too_large"

    big_chart = client.post(RECORDS, json=_payload(chart={"blob": "x" * 600_000}))
    assert big_chart.status_code == 413
    assert big_chart.json()["error"]["code"] == "payload_too_large"

    record = _create(client)
    big_reading = client.put(
        f"{RECORDS}/{record['id']}/reading", json={"text": "字" * 200_001}
    )
    assert big_reading.status_code == 413
    assert big_reading.json()["error"]["code"] == "text_too_large"


def test_rejects_bad_body(client) -> None:
    _signup(client)
    assert client.post(RECORDS, json=_payload(title="标" * 201)).status_code == 422
    assert client.post(RECORDS, json=_payload(system="")).status_code == 422


def test_reading_lifecycle(client) -> None:
    _signup(client)
    record = _create(client)
    url = f"{RECORDS}/{record['id']}/reading"

    assert client.get(url).status_code == 200
    assert client.get(url).json() is None

    saved = client.put(
        url,
        json={
            "text": "## 解读\n\n命格偏财旺。",
            "focus": ["overview", "wealth"],
            "style": "concise",
            "question": "",
            "system": "bazi",
        },
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["text"].startswith("## 解读")
    assert body["focus"] == ["overview", "wealth"]
    assert body["style"] == "concise"
    assert body["system"] == "bazi"
    assert body["updatedAt"] > 1_600_000_000_000

    assert client.get(url).json() == body
    assert client.delete(url).status_code == 204
    assert client.get(url).json() is None
    assert client.delete(url).status_code == 404


def test_reading_overwrites_same_record(client) -> None:
    _signup(client)
    record = _create(client)
    url = f"{RECORDS}/{record['id']}/reading"
    client.put(url, json={"text": "第一版", "focus": ["overview"]})
    second = client.put(url, json={"text": "第二版", "focus": ["career"]}).json()
    assert second["text"] == "第二版"
    assert client.get(url).json()["text"] == "第二版"


def test_reading_focus_is_normalized_to_list(client) -> None:
    _signup(client)
    record = _create(client)
    url = f"{RECORDS}/{record['id']}/reading"
    assert client.put(url, json={"text": "x", "focus": "wealth"}).json()["focus"] == ["wealth"]
    assert client.put(url, json={"text": "x"}).json()["focus"] == []
    too_many = client.put(url, json={"text": "x", "focus": [f"t{i}" for i in range(21)]})
    assert too_many.status_code == 422
    assert too_many.json()["error"]["code"] == "too_many_focus"


def test_reading_of_missing_record_is_404(client) -> None:
    _signup(client)
    url = f"{RECORDS}/nope/reading"
    assert client.get(url).status_code == 404
    assert client.put(url, json={"text": "x"}).status_code == 404
    assert client.delete(url).status_code == 404


def test_reading_is_removed_with_record(client) -> None:
    _signup(client)
    record = _create(client)
    url = f"{RECORDS}/{record['id']}/reading"
    client.put(url, json={"text": "存档"})
    assert client.delete(f"{RECORDS}/{record['id']}").status_code == 204
    assert client.get(url).status_code == 404
