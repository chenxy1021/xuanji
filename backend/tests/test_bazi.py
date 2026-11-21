from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_systems_lists_all() -> None:
    specs = client.get("/api/v1/systems").json()
    ids = {s["id"] for s in specs}
    assert {"bazi", "ziwei", "liuyao", "tarot", "astrology"} <= ids


def test_systems_scope_is_the_final_list() -> None:
    """上线清单已收敛：日运/月运/小六壬/大六壬不应再注册。"""
    ids = [s["id"] for s in client.get("/api/v1/systems").json()]
    assert ids == [
        "bazi",
        "ziwei",
        "astrology",
        "qimen",
        "bazi_hepan",
        "ziwei_hepan",
        "liuyao",
        "tarot",
        "meihua",
        "kongming",
        "mbti",
    ]


def test_bazi_chart_returns_pillars() -> None:
    payload = {
        "birth": {
            "calendar": "solar",
            "year": 1990,
            "month": 5,
            "day": 15,
            "hour": 14,
            "minute": 30,
            "gender": "male",
            "true_solar_time": True,
            "place": {
                "name": "北京市",
                "longitude": 116.407,
                "latitude": 39.904,
                "timezone": 8,
            },
        }
    }
    resp = client.post("/api/v1/charts/bazi", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["system"] == "bazi"
    pillars = body["chart"]["pillars"]
    assert set(pillars) == {"year", "month", "day", "hour"}
    for pillar in pillars.values():
        assert len(pillar["gan"]) == 1
        assert len(pillar["zhi"]) == 1
    assert body["chart"]["true_solar_time"] is not None
    assert "四柱" in body["text"]
    assert body["chart"]["dayun"]


def test_bazi_unknown_time_still_works() -> None:
    payload = {
        "birth": {
            "calendar": "solar",
            "year": 1985,
            "month": 12,
            "day": 1,
            "gender": "female",
            "true_solar_time": False,
        }
    }
    resp = client.post("/api/v1/charts/bazi", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chart"]["pillars"]["hour"]["gan"] == "未知"


def test_unknown_system_404() -> None:
    payload = {"birth": {"year": 1990, "month": 1, "day": 1}}
    resp = client.post("/api/v1/charts/unknown", json=payload)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "unknown_system"


def test_all_systems_are_ready() -> None:
    specs = client.get("/api/v1/systems").json()
    planned = [s["id"] for s in specs if s["status"] != "ready"]
    assert planned == []
