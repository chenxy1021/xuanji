"""奇门终身局：按出生时刻起局，年命/日干/时干三宫用神。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BIRTH = {
    "calendar": "solar",
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 10,
    "minute": 30,
    "gender": "male",
    "true_solar_time": True,
    "place": {"name": "北京", "province": "北京", "longitude": 116.407, "latitude": 39.904, "timezone": 8},
}


def _chart(birth: dict | None = BIRTH) -> dict:
    payload = {"birth": birth} if birth else {}
    resp = client.post("/api/v1/charts/qimen", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["chart"]


def test_qimen_lifelong_structure() -> None:
    chart = _chart()

    assert chart["kind"] == "lifelong"
    assert chart["method"].startswith("奇门终身局")
    assert chart["four_pillars"]["year"] == "庚午"
    assert chart["four_pillars"]["day"] == "庚辰"
    assert chart["four_pillars"]["hour"] == "辛巳"
    assert chart["ju"] == 4
    assert chart["dun"] == "阳遁"
    assert chart["ju_text"] == "阳遁四局"
    assert chart["lifelong"]["zodiac"] == "马"
    assert len(chart["palaces"]) == 9
    assert len(chart["grid"]) == 9


def test_qimen_lifelong_anchors() -> None:
    life = _chart()["lifelong"]

    assert [a["label"] for a in life["anchors"]] == ["年命宫", "日干宫", "时干宫"]
    # 年干庚、日干庚同落乾六宫；时干辛落兑七宫
    assert [a["palace"]["number"] for a in life["anchors"]] == [6, 6, 7]
    for anchor in life["anchors"]:
        assert anchor["basis"] in {"地盘落宫", "地盘寄宫", "甲遁于六仪，以值符所临之宫为用"}
        assert anchor["palace"]["door"]
        assert anchor["summary"]
        assert anchor["relation"]["name"] in {"比和", "宫生干", "干生宫", "宫克干", "干克宫"}
        assert anchor["readings"]


def test_qimen_jia_year_uses_zhifu_palace() -> None:
    """年干为甲时，甲遁于六仪，以值符所临之宫为年命宫。"""
    birth = {**BIRTH, "year": 1984, "month": 6, "day": 1}
    chart = _chart(birth)
    anchor = chart["lifelong"]["year_ming"]
    assert anchor["stem"] == "甲"
    assert anchor["basis"] == "甲遁于六仪，以值符所临之宫为用"
    assert anchor["palace"]["number"] == chart["leaders"]["star_palace"]


def test_qimen_grid_layout() -> None:
    grid = _chart()["grid"]
    assert [p["number"] for p in grid] == [4, 9, 2, 3, 5, 7, 8, 1, 6]
    assert grid[4]["trigram"] == "中"


def test_qimen_requires_birth() -> None:
    resp = client.post("/api/v1/charts/qimen", json={})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "missing_birth"


def test_qimen_requires_time() -> None:
    birth = {k: v for k, v in BIRTH.items() if k not in ("hour", "minute")}
    resp = client.post("/api/v1/charts/qimen", json={"birth": birth})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "engine_error"


def test_qimen_spec_is_chart() -> None:
    spec = {s["id"]: s for s in client.get("/api/v1/systems").json()}["qimen"]
    assert spec["name"] == "奇门终身局"
    assert spec["requires_birth"] is True
    assert spec["requires_time"] is True
    assert spec["category"] == "chart"
    assert spec["fields"] == []
