"""幂等性契约：同一个入参重复请求，盘面与规范文本必须逐字一致。

只有「未给种子/未给时刻」的随机起卦是刻意不幂等的，这里全部显式传入。
"""

from __future__ import annotations

import pytest
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
    "true_solar_time": True,
    "place": {"name": "北京市", "province": "北京", "longitude": 116.4074, "latitude": 39.9042, "timezone": 8},
}
SECONDARY = {
    "calendar": "solar",
    "year": 1992,
    "month": 8,
    "day": 3,
    "hour": 9,
    "minute": 0,
    "gender": "female",
    "true_solar_time": False,
    "place": None,
}

CASES = {
    "bazi": {"birth": BIRTH},
    "ziwei": {"birth": BIRTH},
    "astrology": {"birth": BIRTH},
    "qimen": {"birth": BIRTH},
    "bazi_hepan": {"birth": BIRTH, "secondary": SECONDARY},
    "ziwei_hepan": {"birth": BIRTH, "secondary": SECONDARY},
    "liuyao": {"options": {"method": "time", "date": "2025-03-05", "hour": 14, "minute": 30, "question": "此事可成否"}},
    "tarot": {"options": {"spread": "three", "seed": 42, "question": "今年适合换工作吗"}},
    "meihua": {"options": {"method": "time", "date": "2025-03-05", "hour": 14}},
    "kongming": {"options": {"characters": "佑咱统", "question": "这次换工作能否顺利"}},
    "mbti": {"options": {"answers": [3] * 32}},
}


def _call(system: str, body: dict) -> dict:
    resp = client.post(f"/api/v1/charts/{system}", json=body)
    assert resp.status_code == 200, f"{system}: {resp.status_code} {resp.text}"
    return resp.json()


@pytest.mark.parametrize("system", list(CASES))
def test_same_input_same_chart_and_text(system: str) -> None:
    body = CASES[system]
    first = _call(system, body)
    second = _call(system, body)
    assert first["chart"] == second["chart"], f"{system}: chart 不幂等"
    assert first["text"] == second["text"], f"{system}: text 不幂等"
    assert first["warnings"] == second["warnings"], f"{system}: warnings 不幂等"


def test_repeated_calls_do_not_leak_state_across_systems() -> None:
    """先打别的体系，再回来打同一入参，结果不受影响。"""
    before = _call("bazi", CASES["bazi"])
    _call("astrology", CASES["astrology"])
    _call("liuyao", CASES["liuyao"])
    _call("tarot", CASES["tarot"])
    after = _call("bazi", CASES["bazi"])
    assert before == after
