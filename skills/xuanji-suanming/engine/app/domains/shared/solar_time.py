"""真太阳时校正。

真太阳时 = 当地标准时 + 经度差修正 + 均时差

- 标准子午线：按出生地时区推得，每 1 小时 = 15°（UTC+8 → 120°E，UTC+9 → 135°E）
- 经度差修正：(经度 − 标准子午线) × 4 分钟
- 均时差：太阳真时与平时的差值，年内约 ±16 分钟，用经典近似公式计算，精度约 ±30 秒
  对命理排盘（时辰以两小时为单位）完全足够。

校正后可能跨越日界（尤其子时），因此返回完整 datetime，调用方必须用返回值的日期。
默认标准子午线仍是 120°E（东八区），保持旧调用行为不变。
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

DEFAULT_STANDARD_MERIDIAN = 120.0


def equation_of_time_minutes(moment: datetime) -> float:
    """均时差（分钟）。moment 必须是当地平太阳时意义上的时刻。"""
    day_of_year = moment.timetuple().tm_yday
    b = 2 * math.pi * (day_of_year - 81) / 364.0
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def standard_meridian_for(timezone_hours: float) -> float:
    """按 UTC 偏移推标准子午线：每 1 小时 = 15°（可处理半小时时区，如 UTC+5:30 → 82.5°）。"""
    return round(float(timezone_hours) * 15.0, 4)


def timezone_label(timezone_hours: float) -> str:
    """UTC 偏移的展示写法：UTC+8 / UTC-5 / UTC+5:30。"""
    tz = float(timezone_hours)
    sign = "+" if tz >= 0 else "-"
    hours, minutes = divmod(round(abs(tz) * 60), 60)
    if minutes:
        return f"UTC{sign}{hours}:{minutes:02d}"
    return f"UTC{sign}{hours}"


def longitude_correction_minutes(
    longitude: float, standard_meridian: float = DEFAULT_STANDARD_MERIDIAN
) -> float:
    """经度差修正（分钟）：每偏离标准子午线 1 度 = 4 分钟。"""
    return (longitude - standard_meridian) * 4.0


def to_true_solar_time(
    local_clock: datetime,
    longitude: float,
    standard_meridian: float = DEFAULT_STANDARD_MERIDIAN,
) -> datetime:
    """把当地钟表时转换为真太阳时。"""
    correction = longitude_correction_minutes(longitude, standard_meridian)
    correction += equation_of_time_minutes(local_clock)
    return local_clock + timedelta(minutes=correction)


def solar_time_info(
    local_clock: datetime,
    longitude: float,
    standard_meridian: float = DEFAULT_STANDARD_MERIDIAN,
) -> dict[str, object]:
    """给前端展示用的校正明细（保留原有字段，新增 standard_meridian）。"""
    lon_corr = longitude_correction_minutes(longitude, standard_meridian)
    eot = equation_of_time_minutes(local_clock)
    return {
        "clock_time": local_clock.strftime("%Y-%m-%d %H:%M"),
        "longitude_correction_minutes": round(lon_corr, 2),
        "equation_of_time_minutes": round(eot, 2),
        "total_correction_minutes": round(lon_corr + eot, 2),
        "standard_meridian": round(float(standard_meridian), 2),
        "true_solar_time": (local_clock + timedelta(minutes=lon_corr + eot)).strftime(
            "%Y-%m-%d %H:%M"
        ),
    }
