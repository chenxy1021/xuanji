from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

A = {
    "calendar": "solar",
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "gender": "male",
    "true_solar_time": True,
    "place": {"name": "北京市", "longitude": 116.407, "latitude": 39.904, "timezone": 8},
}

B = {
    "calendar": "solar",
    "year": 1992,
    "month": 8,
    "day": 3,
    "hour": 9,
    "minute": 20,
    "gender": "female",
    "true_solar_time": True,
    "place": {"name": "上海市", "longitude": 121.474, "latitude": 31.230, "timezone": 8},
}


def test_systems_include_synastry() -> None:
    specs = client.get("/api/v1/systems").json()
    by_id = {s["id"]: s for s in specs}
    assert by_id["bazi_hepan"]["requires_secondary"] is True
    assert by_id["ziwei_hepan"]["requires_secondary"] is True
    assert by_id["bazi_hepan"]["category"] == "synastry"


def test_bazi_hepan_requires_secondary() -> None:
    resp = client.post("/api/v1/charts/bazi_hepan", json={"birth": A})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "missing_secondary"


def test_bazi_hepan_structure() -> None:
    resp = client.post("/api/v1/charts/bazi_hepan", json={"birth": A, "secondary": B})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    chart = body["chart"]

    assert body["system"] == "bazi_hepan"
    assert 0 <= chart["score"] <= 100
    assert chart["level"]
    assert len(chart["a"]["day_master"]) == 1
    assert len(chart["b"]["day_master"]) == 1
    assert sum(chart["a"]["wuxing"].values()) > 0
    assert chart["matches"]
    assert any(m["scope"] == "日主" for m in chart["matches"])
    assert chart["advice"]
    assert "八字合盘" in body["text"]


def test_ziwei_hepan_requires_secondary() -> None:
    resp = client.post("/api/v1/charts/ziwei_hepan", json={"birth": A})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "missing_secondary"


def test_ziwei_hepan_structure() -> None:
    resp = client.post("/api/v1/charts/ziwei_hepan", json={"birth": A, "secondary": B})
    assert resp.status_code == 200, resp.text
    chart = resp.json()["chart"]

    assert 0 <= chart["score"] <= 100
    assert len(chart["a"]["palaces"]) == 12
    assert len(chart["b"]["palaces"]) == 12
    assert len(chart["a"]["ming_branch"]) == 1
    assert "紫微合盘" in resp.json()["text"]
    # 命宫地支关系一定有一条记录
    assert any(m["scope"] == "命宫" for m in chart["matches"])


def test_ziwei_hepan_needs_time() -> None:
    no_time = {k: v for k, v in A.items() if k not in ("hour", "minute")}
    resp = client.post("/api/v1/charts/ziwei_hepan", json={"birth": no_time, "secondary": B})
    assert resp.status_code == 422
