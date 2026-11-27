"""西方占星：本命盘（热带黄道、普拉西度分宫）。

星体位置由 Swiss Ephemeris（pyswisseph）计算，精度到角秒级。
注意：西方占星使用**钟表时 + 经度/纬度**，不套用中国命理的真太阳时。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import swisseph as swe

from app.core.errors import EngineError
from app.core.types import BirthInput
from app.domains.shared.calendar import resolve_solar_date

ENGINE_VERSION = "astrology-1.0"

SIGNS = ("白羊", "金牛", "双子", "巨蟹", "狮子", "处女", "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼")
ELEMENTS = ("火", "土", "风", "水")
MODES = ("基本", "固定", "变动")

_PLANETS: tuple[tuple[str, int], ...] = (
    ("太阳", swe.SUN),
    ("月亮", swe.MOON),
    ("水星", swe.MERCURY),
    ("金星", swe.VENUS),
    ("火星", swe.MARS),
    ("木星", swe.JUPITER),
    ("土星", swe.SATURN),
    ("天王星", swe.URANUS),
    ("海王星", swe.NEPTUNE),
    ("冥王星", swe.PLUTO),
)

_ASPECTS: tuple[tuple[str, float, float], ...] = (
    ("合相", 0.0, 8.0),
    ("对冲", 180.0, 8.0),
    ("三分相", 120.0, 7.0),
    ("四分相", 90.0, 7.0),
    ("六分相", 60.0, 5.0),
)


def compute(birth: BirthInput) -> tuple[dict[str, Any], str, list[str]]:
    warnings: list[str] = []
    solar_date: date = resolve_solar_date(birth)
    hour, minute = birth.resolved_hour_minute()
    time_known = hour is not None

    if not time_known:
        # 太阳星座只需日期，仍可给出；其余按当日正午近似
        hour, minute = 12, 0
        warnings.append("未提供出生时刻：上升星座与宫位不可用，行星位置按当日正午估算")

    tz = birth.place.timezone if birth.place else 8.0
    local_dt = datetime(solar_date.year, solar_date.month, solar_date.day, hour, minute or 0)
    utc_dt = local_dt - timedelta(hours=tz)
    jd_ut = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0,
    )

    positions: list[dict[str, Any]] = []
    for name, pid in _PLANETS:
        try:
            values, _flags = swe.calc_ut(jd_ut, pid)
        except swe.Error as exc:  # pragma: no cover - 仅星历缺文件时触发
            raise EngineError(f"星体计算失败（{name}）：{exc}") from exc
        longitude, _lat, _dist, speed = values[0], values[1], values[2], values[3]
        positions.append(
            {
                "name": name,
                "longitude": round(longitude, 4),
                "sign": _sign_of(longitude),
                "degree_in_sign": round(longitude % 30, 2),
                "retrograde": speed < 0,
            }
        )

    houses: list[float] | None = None
    ascmc: tuple[float, ...] | None = None
    if time_known and birth.place is not None:
        try:
            cusps, ascmc = swe.houses(jd_ut, birth.place.latitude, birth.place.longitude, b"P")
            houses = list(cusps)
        except swe.Error:  # pragma: no cover - 高纬度（约 |lat| ≥ 66.6°）普拉西度无解
            warnings.append(
                "出生地纬度过高，普拉西度分宫无法计算：上升与宫位暂不可用，日月行星落座仍可参考"
            )
    elif time_known:
        warnings.append("未提供出生地经纬度，无法计算上升星座与宫位")

    for planet in positions:
        planet["house"] = _house_of(planet["longitude"], houses) if houses else None

    chart: dict[str, Any] = {
        "engine": ENGINE_VERSION,
        "utc_time": utc_dt.strftime("%Y-%m-%d %H:%M"),
        "local_time": local_dt.strftime("%Y-%m-%d %H:%M"),
        "timezone": tz,
        "place": birth.place.name if birth.place else None,
        "zodiac": "热带黄道",
        "house_system": "普拉西度",
        "sun": _summary(_find(positions, "太阳")),
        "moon": _summary(_find(positions, "月亮")),
        "rising": None,
        "mc": None,
        "planets": positions,
        "aspects": _aspects(positions),
        "balance": _balance(positions),
    }
    if ascmc is not None:
        chart["rising"] = {
            "sign": _sign_of(ascmc[0]),
            "degree_in_sign": round(ascmc[0] % 30, 2),
        }
        chart["mc"] = {
            "sign": _sign_of(ascmc[1]),
            "degree_in_sign": round(ascmc[1] % 30, 2),
        }

    return chart, "", warnings


def _sign_of(longitude: float) -> str:
    return SIGNS[int(longitude % 360 // 30)]


def _sign_index(longitude: float) -> int:
    return int(longitude % 360 // 30)


def _find(positions: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(p for p in positions if p["name"] == name)


def _summary(planet: dict[str, Any]) -> dict[str, Any]:
    index = _sign_index(planet["longitude"])
    return {
        "sign": planet["sign"],
        "degree_in_sign": planet["degree_in_sign"],
        "element": ELEMENTS[index % 4],
        "mode": MODES[index % 3],
    }


def _house_of(longitude: float, cusps: list[float]) -> int | None:
    # pyswisseph 返回 12 个宫头，索引 0 对应第 1 宫
    if len(cusps) < 12:
        return None
    lon = longitude % 360
    for i in range(12):
        start = cusps[i] % 360
        end = cusps[(i + 1) % 12] % 360
        if start <= end:
            if start <= lon < end:
                return i + 1
        elif lon >= start or lon < end:
            return i + 1
    return None


def _aspects(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for i, a in enumerate(positions):
        for b in positions[i + 1 :]:
            diff = abs(a["longitude"] - b["longitude"]) % 360
            if diff > 180:
                diff = 360 - diff
            for name, angle, orb in _ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    result.append(
                        {
                            "a": a["name"],
                            "b": b["name"],
                            "type": name,
                            "angle": angle,
                            "orb": round(delta, 2),
                        }
                    )
                    break
    result.sort(key=lambda x: x["orb"])
    return result


def _balance(positions: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    elements = dict.fromkeys(ELEMENTS, 0)
    modes = dict.fromkeys(MODES, 0)
    # 只统计日月与内行星，外行星影响太慢、参考价值低
    for planet in positions[:7]:
        index = _sign_index(planet["longitude"])
        elements[ELEMENTS[index % 4]] += 1
        modes[MODES[index % 3]] += 1
    return {"elements": elements, "modes": modes}
