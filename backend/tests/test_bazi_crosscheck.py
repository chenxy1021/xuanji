"""四柱交叉校验：本项目引擎 vs lunar_python 的独立实现。

口径说明：本项目采用「晚子时（23:00 起）归次日」，
对应 lunar_python 的 `getDayInGanZhiExact()`；默认的 getDayInGanZhi 以 00:00 换日，不用。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from lunar_python import Solar

from app.main import app

client = TestClient(app)

# 覆盖：普通日、立春前后、23:00 日界、闰月年、元旦
SAMPLES = [
    (1990, 5, 15, 14, 30),
    (1990, 2, 3, 10, 0),
    (1990, 2, 4, 10, 0),
    (2024, 2, 4, 16, 0),
    (2024, 2, 4, 17, 0),
    (2000, 1, 1, 0, 30),
    (2000, 1, 1, 23, 30),
    (1984, 2, 2, 12, 0),
    (2025, 12, 31, 23, 10),
    (2023, 3, 22, 8, 15),
]


def _ours(y: int, m: int, d: int, h: int, mi: int) -> list[str]:
    resp = client.post(
        "/api/v1/charts/bazi",
        json={
            "birth": {
                "calendar": "solar",
                "year": y,
                "month": m,
                "day": d,
                "hour": h,
                "minute": mi,
                "is_leap_month": False,
                "gender": "male",
                "true_solar_time": False,
                "place": None,
            },
            "options": {},
        },
    )
    assert resp.status_code == 200, resp.text
    p = resp.json()["chart"]["pillars"]
    return [
        p["year"]["gan"] + p["year"]["zhi"],
        p["month"]["gan"] + p["month"]["zhi"],
        p["day"]["gan"] + p["day"]["zhi"],
        p["hour"]["gan"] + p["hour"]["zhi"],
    ]


def _reference(y: int, m: int, d: int, h: int, mi: int) -> list[str]:
    lunar = Solar.fromYmdHms(y, m, d, h, mi, 0).getLunar()
    eight = lunar.getEightChar()
    return [eight.getYear(), eight.getMonth(), lunar.getDayInGanZhiExact(), eight.getTime()]


@pytest.mark.parametrize("sample", SAMPLES)
def test_pillars_match_lunar_python(sample: tuple[int, int, int, int, int]) -> None:
    assert _ours(*sample) == _reference(*sample), f"{sample} 四柱与 lunar_python 不一致"
