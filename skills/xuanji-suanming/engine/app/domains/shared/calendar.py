"""公历 / 农历互转，基于 lunar_python（lunar-javascript 的官方 Python 移植）。"""

from __future__ import annotations

from datetime import date

from lunar_python import Lunar, Solar

from app.core.errors import EngineError
from app.core.types import BirthInput


def solar_to_lunar_text(solar_date: date) -> str:
    solar = Solar.fromYmd(solar_date.year, solar_date.month, solar_date.day)
    return solar.getLunar().toString()


def lunar_to_solar(year: int, month: int, day: int, is_leap: bool = False) -> date:
    """农历转公历。lunar_python 用负月份表示闰月。"""
    try:
        lunar = Lunar.fromYmd(year, -month if is_leap else month, day)
        solar = lunar.getSolar()
    except Exception as exc:  # noqa: BLE001 - 第三方库抛的是通用异常
        raise EngineError(f"农历日期无效：{year}年{'闰' if is_leap else ''}{month}月{day}日") from exc
    return date(solar.getYear(), solar.getMonth(), solar.getDay())


def lunar_month_days(year: int, month: int, is_leap: bool = False) -> int:
    """某农历月的天数，供前端日期选择器使用。"""
    lunar = Lunar.fromYmd(year, -month if is_leap else month, 1)
    return lunar.getMonthDayCount() if hasattr(lunar, "getMonthDayCount") else 30


def resolve_solar_date(birth: BirthInput) -> date:
    """把 BirthInput 的日期部分统一换算成公历。"""
    if birth.calendar == "lunar":
        return lunar_to_solar(birth.year, birth.month, birth.day, birth.is_leap_month)
    try:
        return date(birth.year, birth.month, birth.day)
    except ValueError as exc:
        raise EngineError(f"公历日期无效：{birth.year}-{birth.month}-{birth.day}") from exc
