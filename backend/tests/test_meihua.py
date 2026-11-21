"""梅花易数起卦测试：时间/数字起卦、互变卦、体用生克、六十四卦表完整性、非法输入。"""

from fastapi.testclient import TestClient

from app.domains.meihua import constants as C
from app.domains.meihua import engine
from app.main import app

client = TestClient(app)


def _chart(**options):
    return client.post("/api/v1/charts/meihua", json={"options": options})


def test_time_method_kan_hexagram() -> None:
    """2025-03-05 未时：上卦 (6+2+6)=14%8=6 坎，下卦 (14+8)=22%8=6 坎，动爻 22%6=4。"""
    body = _chart(method="time", date="2025-03-05", hour=14).json()
    chart = body["chart"]

    assert chart["method"] == "time"
    assert chart["cast"]["upper_mod"] == 6
    assert chart["cast"]["lower_mod"] == 6
    assert chart["ben"]["name"] == "坎为水"
    assert chart["moving_line"] == 4
    assert chart["bian"]["name"] == "泽水困"
    assert chart["hu"]["name"] == "山雷颐"
    # 动爻在上卦 -> 下卦坎为体、上卦坎为用，两坎比和
    assert chart["ti_yong"]["ti"]["trigram"] == "坎"
    assert chart["ti_yong"]["yong"]["trigram"] == "坎"
    assert chart["relation"]["name"] == "体用比和"
    assert chart["relation"]["result"] == "吉"
    assert "坎为水" in body["text"] and "体用" in body["text"]


def test_number_method_zhongfu_hexagram() -> None:
    """37%8=5 巽为上卦，18%8=2 兑为下卦，动爻 (37+18)%6=1 -> 风泽中孚，用克体为凶。"""
    chart = engine.compute({"method": "number", "numbers": [37, 18]})

    assert chart["ben"]["name"] == "风泽中孚"
    assert (chart["ben"]["upper"], chart["ben"]["lower"]) == ("巽", "兑")
    assert chart["moving_line"] == 1
    assert chart["hu"]["name"] == "山雷颐"
    assert chart["bian"]["name"] == "风水涣"
    # 动爻在下卦 -> 上卦巽（木）为体、下卦兑（金）为用，金克木
    assert chart["ti_yong"]["ti"]["element"] == "木"
    assert chart["ti_yong"]["yong"]["element"] == "金"
    assert chart["relation"]["code"] == "yong_ke_ti"
    assert chart["relation"]["result"] == "凶"


def test_relation_levels_are_enumerated() -> None:
    seen = set()
    for first in range(1, 40):
        for second in range(1, 40):
            relation = engine.compute({"method": "number", "numbers": [first, second]})["relation"]
            assert relation["result"] in C.RELATION_LEVELS
            seen.add(relation["code"])
    assert seen <= set(C.RELATION_TEXT)
    assert "yong_sheng_ti" in seen and "yong_ke_ti" in seen


def test_hexagram_table_is_complete() -> None:
    assert len(C.HEXAGRAMS) == 64
    assert len(C.KING_WEN_ORDER) == 64
    assert {item["name"] for item in C.HEXAGRAMS.values()} == set(C.KING_WEN_ORDER)
    # 6 位卦画与上下卦一致
    for code, item in C.HEXAGRAMS.items():
        lower = C.BINARY_TO_TRIGRAM[tuple(int(bit) for bit in code[0:3])]
        upper = C.BINARY_TO_TRIGRAM[tuple(int(bit) for bit in code[3:6])]
        if upper == lower:
            expected = f"{upper}为{C.TRIGRAMS[upper]['nature']}"
        else:
            expected = f"{C.TRIGRAMS[upper]['nature']}{C.TRIGRAMS[lower]['nature']}{item['name'][2:]}"
        assert item["name"] == expected, code
        assert item["yixiang"], code


def test_default_options_use_time_method() -> None:
    chart = engine.compute({})
    assert chart["method"] == "time"
    for key in ("ben", "hu", "bian"):
        assert chart[key]["name"] in C.KING_WEN_ORDER
        assert chart[key]["yixiang"]
    assert chart["judgement"] and len(chart["judgement"]) >= 30


def test_invalid_input_raises_engine_error() -> None:
    bad_numbers = _chart(method="number", numbers=[1])
    assert bad_numbers.status_code == 422
    assert bad_numbers.json()["error"]["code"] == "engine_error"

    bad_method = _chart(method="乱写")
    assert bad_method.status_code == 422

    bad_date = _chart(method="time", date="昨天")
    assert bad_date.status_code == 422


def test_numbers_accepts_string_from_form() -> None:
    """前端通用表单会把 numbers 当字符串提交，需与 list 等价。"""
    baseline = engine.compute({"method": "number", "numbers": [37, 18]})
    for raw in ("37,18", "37，18", "37 18", "37、18", "37+18", " 37 , 18 ", "37;18", "37\n18"):
        chart = engine.compute({"method": "number", "numbers": raw})
        assert chart["ben"]["name"] == baseline["ben"]["name"], raw
        assert chart["moving_line"] == baseline["moving_line"], raw
        assert (chart["cast"]["upper_number"], chart["cast"]["lower_number"]) == (37, 18), raw


def test_missing_or_wrong_numbers_message() -> None:
    missing = _chart(method="number")
    assert missing.status_code == 422
    body = missing.json()["error"]
    assert body["code"] == "engine_error"
    assert "数字起卦需要填写两个数字" in body["message"]

    too_many = _chart(method="number", numbers="1,2,3")
    assert too_many.status_code == 422
    assert "两个数字" in too_many.json()["error"]["message"]

    not_int = _chart(method="number", numbers="37,abc")
    assert not_int.status_code == 422
    assert "整数" in not_int.json()["error"]["message"]


def test_registry_entry_and_fields() -> None:
    systems = {item["id"]: item for item in client.get("/api/v1/systems").json()}
    spec = systems["meihua"]
    assert spec["status"] == "ready"
    assert spec["category"] == "divination"
    assert spec["requires_birth"] is False
    assert {field["key"] for field in spec["fields"]} >= {"method", "numbers", "date"}
