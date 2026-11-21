from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _post(birth: dict):
    return client.post("/api/v1/charts/ziwei", json={"birth": birth})


BASE = {
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


def test_ziwei_chart_structure() -> None:
    resp = _post(BASE)
    assert resp.status_code == 200, resp.text
    chart = resp.json()["chart"]

    assert chart["bureau"] == "土五局"
    assert chart["ming_gong"] == "戌"
    assert len(chart["palaces"]) == 12
    assert {p["branch"] for p in chart["palaces"]} == set("子丑寅卯辰巳午未申酉戌亥")

    # 命宫在戌，紫微同宫
    xu = next(p for p in chart["palaces"] if p["branch"] == "戌")
    assert xu["name"] == "命宫"
    assert any(s["name"] == "紫微" for s in xu["stars"])

    # 庚年四化：太阳禄、武曲权、天同科、太阴忌
    assert chart["sihua"] == {"禄": "太阳", "权": "武曲", "科": "天同", "忌": "太阴"}

    assert len(chart["decades"]) == 12
    assert chart["decades"][0]["start_age"] == 5


def test_ziwei_requires_birth_time() -> None:
    birth = {k: v for k, v in BASE.items() if k not in {"hour", "minute"}}
    resp = _post(birth)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "engine_error"


def test_ziwei_unknown_hour_falls_back_to_shichen() -> None:
    birth = {k: v for k, v in BASE.items() if k not in {"hour", "minute"}}
    birth["shichen"] = "未"
    resp = _post(birth)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["chart"]["palaces"]) == 12


def test_ziwei_late_zi_hour() -> None:
    birth = {**BASE, "hour": 23, "minute": 30}
    resp = _post(birth)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["chart"]["palaces"]) == 12


def test_ziwei_leap_month() -> None:
    birth = {**BASE, "year": 2020, "month": 6, "day": 1, "hour": 9, "minute": 0}
    resp = _post(birth)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["chart"]["palaces"]) == 12
    assert "闰" in body["chart"]["lunar_date"]


def test_ziwei_text_renders() -> None:
    resp = _post(BASE)
    body = resp.json()
    assert "十二宫" in body["text"]
    assert "紫微斗数命盘" in body["text"]
    assert body["engine_version"].startswith("ziwei-")
