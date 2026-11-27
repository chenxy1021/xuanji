"""把「起课时刻」统一解析成 datetime。

占卜类体系（奇门、大六壬）既可以直接指定时刻，也可以沿用出生信息；
两者都没有时按当前时间起课。
"""

from __future__ import annotations

from datetime import date, datetime, time

from app.core.errors import EngineError
from app.core.types import BirthInput
from app.domains.shared.calendar import resolve_solar_date
from app.domains.shared.solar_time import (
    solar_time_info,
    standard_meridian_for,
    timezone_label,
    to_true_solar_time,
)

_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M")


def resolve_moment(
    birth: BirthInput | None, options: dict | None, *, apply_true_solar_time: bool = True
) -> tuple[datetime, list[str]]:
    options = options or {}
    warnings: list[str] = []

    raw = options.get("datetime") or options.get("moment")
    if raw:
        return _parse(raw), warnings

    if birth is None:
        return datetime.now().replace(second=0, microsecond=0), ["未指定时刻，按当前时间起课"]

    solar_date: date = resolve_solar_date(birth)
    hour, minute = birth.resolved_hour_minute()
    if hour is None:
        raise EngineError("该体系需要具体时刻，请至少选择时辰")

    moment = datetime.combine(solar_date, time(hour, minute or 0))

    if apply_true_solar_time and birth.true_solar_time and birth.place is not None:
        # 与八字一致：标准子午线按出生地时区推，国外出生不再套用东八区
        meridian = standard_meridian_for(birth.place.timezone)
        moment = to_true_solar_time(moment, birth.place.longitude, meridian)
        info = solar_time_info(
            datetime.combine(solar_date, time(hour, minute or 0)),
            birth.place.longitude,
            meridian,
        )
        warnings.append(
            f"已按真太阳时校正（按 {timezone_label(birth.place.timezone)} 标准时，"
            f"经度 {birth.place.longitude:.3f}°、基准子午线 {meridian:.1f}°，"
            f"合计 {info['total_correction_minutes']} 分钟）"
        )

    return moment, warnings


def _parse(raw: object) -> datetime:
    text = str(raw).strip()
    for fmt in _FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise EngineError(f"时刻格式应为 YYYY-MM-DD HH:MM：{text}")
