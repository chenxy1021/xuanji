"""孔明神卦（诸葛神数）：三字取康熙笔画 → 384 签。"""

from fastapi.testclient import TestClient

from app.domains.kongming import data, engine
from app.main import app

client = TestClient(app)


def _chart(**options):
    return client.post("/api/v1/charts/kongming", json={"options": options})


def test_known_example() -> None:
    """通行本示例：佑咱统 → 7/9/2 → 792 − 384 − 384 = 24。"""
    chart = engine.compute({"characters": "佑咱统", "question": "工作"})

    assert chart["strokes"] == [7, 9, 12]
    assert chart["digits"] == [7, 9, 2]
    assert chart["calculation"]["raw"] == 792
    assert chart["calculation"]["number"] == 24
    assert chart["lot"]["number"] == 24
    assert chart["lot"]["fortune"] == "中下签"
    assert chart["lot"]["hexagram"] == "同人"
    assert chart["lot"]["line"] == "同人九四"
    assert chart["lot"]["poem"].startswith("意孜孜")


def test_simplified_is_converted_to_traditional() -> None:
    chart = engine.compute({"characters": "陈学国"})
    assert chart["counted_characters"] == ["陳", "學", "國"]
    assert chart["strokes"] == [16, 16, 11]


def test_zero_digits_fall_to_lot_384() -> None:
    chart = engine.compute({"characters": "修高借"})
    assert chart["digits"] == [0, 0, 0]
    assert chart["lot"]["number"] == 384
    assert "384" in chart["calculation"]["detail"]


def test_exactly_384_keeps_384() -> None:
    chart = engine.compute({"characters": "三金文"})
    assert chart["calculation"]["raw"] == 384
    assert chart["lot"]["number"] == 384


def test_all_384_lots_are_complete() -> None:
    assert data.lot_count() == 384
    for number in range(1, 385):
        row = data.lot(number)
        assert row is not None
        assert row["poem"]
        assert row["fortune"].endswith("签")
        assert row["hexagram"] and row["line"]


def test_requires_exactly_three_characters() -> None:
    too_few = _chart(characters="孔明")
    assert too_few.status_code == 422
    assert "三个汉字" in too_few.json()["error"]["message"]

    too_many = _chart(characters="孔明神卦")
    assert too_many.status_code == 422
    assert "只需三个字" in too_many.json()["error"]["message"]

    missing = _chart()
    assert missing.status_code == 422


def test_endpoint_and_spec() -> None:
    body = _chart(characters="佑咱统", question="这份工作要不要接？").json()
    assert body["system"] == "kongming"
    assert body["chart"]["calculation"]["number"] == 24
    assert body["chart"]["question"] == "这份工作要不要接？"
    assert "第 24 签" in body["text"]

    spec = {s["id"]: s for s in client.get("/api/v1/systems").json()}["kongming"]
    assert spec["name"] == "孔明神卦"
    assert spec["category"] == "divination"
    assert spec["requires_birth"] is False
    assert {f["key"] for f in spec["fields"]} == {"question", "characters"}
