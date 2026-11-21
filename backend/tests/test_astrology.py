from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BIRTH = {
    "calendar": "solar",
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "gender": "male",
    "true_solar_time": False,
    "place": {"name": "北京市", "longitude": 116.407, "latitude": 39.904, "timezone": 8},
}


def test_astrology_chart() -> None:
    resp = client.post("/api/v1/charts/astrology", json={"birth": BIRTH})
    assert resp.status_code == 200, resp.text
    chart = resp.json()["chart"]

    assert chart["sun"]["sign"] == "金牛"
    assert 20 <= chart["sun"]["degree_in_sign"] <= 30
    assert chart["rising"] is not None
    assert len(chart["planets"]) == 10
    for planet in chart["planets"]:
        assert planet["house"] is not None
    assert chart["aspects"]


def test_astrology_without_time_degrades() -> None:
    birth = {k: v for k, v in BIRTH.items() if k not in {"hour", "minute"}}
    resp = client.post("/api/v1/charts/astrology", json={"birth": birth})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chart"]["rising"] is None
    assert body["chart"]["sun"]["sign"] == "金牛"
    assert any("上升" in w for w in body["warnings"])


def test_astrology_without_place_degrades() -> None:
    birth = {k: v for k, v in BIRTH.items() if k != "place"}
    resp = client.post("/api/v1/charts/astrology", json={"birth": birth})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chart"]["rising"] is None
    assert body["chart"]["mc"] is None
    assert all(p["house"] is None for p in body["chart"]["planets"])
    assert body["chart"]["sun"]["sign"] == "金牛"
    assert any("出生地" in w for w in body["warnings"])


def test_astrology_high_latitude_degrades() -> None:
    birth = {
        **BIRTH,
        "place": {"name": "特罗姆瑟", "longitude": 18.955, "latitude": 69.649, "timezone": 1},
    }
    resp = client.post("/api/v1/charts/astrology", json={"birth": birth})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chart"]["rising"] is None
    assert all(p["house"] is None for p in body["chart"]["planets"])
    assert body["chart"]["planets"]
    warning = " ".join(body["warnings"])
    assert "纬度" in warning or "分宫" in warning
    assert "swisseph" not in warning


def test_astrology_text() -> None:
    body = client.post("/api/v1/charts/astrology", json={"birth": BIRTH}).json()
    assert "西方占星本命盘" in body["text"]
    assert "行星落座" in body["text"]
