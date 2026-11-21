"""六爻纳甲排盘测试：三种起卦 + 静卦 + 契约校验。"""

from fastapi.testclient import TestClient

from app.domains.liuyao import engine
from app.main import app

client = TestClient(app)

BASE = {"date": "2025-03-05", "hour": 14}

def _chart(**options):
    return client.post("/api/v1/charts/liuyao", json={"options": options})

def test_coins_method_full_chart() -> None:
    """指定六爻起卦：老阳动于初爻，本卦火雷噬嗑，变卦火地晋。"""
    body = _chart(method="coins", lines=[9, 8, 8, 7, 8, 7], question="此事可成否", **BASE).json()
    chart = body["chart"]

    assert chart["method"] == "coins"
    assert chart["moving_lines"] == [1]

    ben = chart["ben_gua"]
    assert ben["name"] == "噬嗑"
    assert ben["full_name"] == "火雷噬嗑"
    assert ben["palace"] == "巽"
    assert ben["element"] == "木"
    assert (ben["shi_line"], ben["ying_line"]) == (5, 2)
    assert len(ben["lines"]) == 6

    # 纳甲：下震庚子/庚寅/庚辰，上离己酉/己未/己巳
    assert [line["gan_zhi"] for line in ben["lines"]] == [
        "庚子", "庚寅", "庚辰", "己酉", "己未", "己巳",
    ]
    # 六亲按巽宫木论：水生木为父母，木为兄弟，木克土为妻财；金克木为官鬼，木生火为子孙
    assert [line["liuqin"] for line in ben["lines"]] == [
        "父母", "兄弟", "妻财", "官鬼", "妻财", "子孙",
    ]
    # 日干癸 -> 初爻起玄武
    assert [line["liushen"] for line in ben["lines"]] == [
        "玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎",
    ]
    # 动爻：初爻动，其余静
    assert [line["moving"] for line in ben["lines"]] == [True, False, False, False, False, False]
    # 世在第一行（五爻）标"世"，二爻标"应"
    assert [line["shi_ying"] for line in ben["lines"]] == [None, "应", None, None, "世", None]

    assert chart["bian_gua"]["name"] == "晋"
    assert chart["bian_gua"]["full_name"] == "火地晋"
    assert chart["bian_gua"]["lines"][0]["yinyang"] == "阴"
    assert all(not line["moving"] for line in chart["bian_gua"]["lines"])

    # 互卦：2/3/4 爻为艮，3/4/5 爻为坎 -> 水山蹇
    assert chart["hu_gua"]["full_name"] == "水山蹇"

    assert body["warnings"]
    assert "六爻纳甲" in body["text"]
    assert "火雷噬嗑" in body["text"]
    assert "此事可成否" in body["text"]

def test_time_method_kan_wei_shui() -> None:
    """时间起卦：2025-03-05 14:00 -> 乙巳年(巳=6)+农历二月+初六 = 14，14%8=6 为坎；加未时(8) 得 22，动四爻。"""
    chart = _chart(method="time", **BASE).json()["chart"]

    assert chart["year_gan_zhi"] == "乙巳"
    assert chart["month_gan_zhi"] == "戊寅"  # 惊蛰前，仍是寅月
    assert chart["day_gan_zhi"] == "癸酉"
    assert chart["ben_gua"]["full_name"] == "坎为水"
    assert chart["moving_lines"] == [4]
    assert chart["bian_gua"]["full_name"] == "泽水困"

def test_number_method_ding_hexagram() -> None:
    """数字起卦：3 -> 上卦离，5 -> 下卦巽，(3+5)%6=2 动二爻 -> 火风鼎。"""
    chart = _chart(method="number", numbers=[3, 5]).json()["chart"]

    assert chart["ben_gua"]["full_name"] == "火风鼎"
    assert chart["ben_gua"]["palace"] == "离"
    assert chart["moving_lines"] == [2]
    assert chart["bian_gua"]["full_name"] == "火山旅"

def test_static_hexagram_has_no_bian_gua() -> None:
    """全静卦：没有动爻时变卦为 null。"""
    chart = _chart(method="coins", lines=[7, 7, 8, 8, 7, 8]).json()["chart"]

    assert chart["moving_lines"] == []
    assert chart["bian_gua"] is None
    # 兑下坎上 -> 水泽节，坎宫一世卦，世初应四
    assert chart["ben_gua"]["full_name"] == "水泽节"
    assert chart["ben_gua"]["stage"] == "一世"
    assert (chart["ben_gua"]["shi_line"], chart["ben_gua"]["ying_line"]) == (1, 4)

def test_registry_shows_liuyao_ready() -> None:
    systems = {item["id"]: item for item in client.get("/api/v1/systems").json()}
    assert systems["liuyao"]["status"] == "ready"
    assert systems["liuyao"]["requires_birth"] is False
    assert systems["liuyao"]["requires_time"] is False

def test_empty_options_defaults_to_time_method() -> None:
    body = client.post("/api/v1/charts/liuyao", json={"options": {}})
    assert body.status_code == 200, body.text
    assert body.json()["chart"]["method"] == "time"


def test_invalid_lines_raise_engine_error() -> None:
    resp = _chart(method="coins", lines=[1, 2, 3, 4, 5, 6])
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "engine_error"

def test_engine_is_pure_and_deterministic() -> None:
    options = {"method": "coins", "lines": [6, 7, 8, 9, 7, 6], **BASE}
    assert engine.compute(options) == engine.compute(options)
