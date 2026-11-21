"""紫微斗数排盘适配层。

排盘规则来自 MIT 许可的 `ziwei` 库（https://github.com/0xf3cd/ziwei），
本文件只负责：统一入参 → 选择主流口径 → 转换为 canonical JSON。
库内已按天文算法处理真太阳时（传入经度即启用），因此这里不再自行校正。
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from ziwei.birth import Gender, GregorianBirthRecord, TimePrecision
from ziwei.brightness import BrightnessTable
from ziwei.chart import chart_brightness, create_chart
from ziwei.config import ChartConfig, DayRollover, LeapMonthPolicy, YearBoundary
from ziwei.sihua import SihuaVariant
from ziwei.timezone import FixedOffset

from app.core.errors import EngineError
from app.core.types import BirthInput
from app.domains.shared.calendar import resolve_solar_date, solar_to_lunar_text
from app.domains.shared.solar_time import timezone_label

from .constants import BRANCH_ORDER, HUA_NAMES, PALACE_NAME_MODERN, star_kind

ENGINE_VERSION = "ziwei-0.5.0"
BEIJING = FixedOffset(timedelta(hours=8))

# 主流排盘口径：闰月中分界、晚子时归次日、农历正月初一换年、四化用排命盘口诀表
CONFIG = ChartConfig(
    leap_month_policy=LeapMonthPolicy.SPLIT_MONTH,
    day_rollover=DayRollover.LATE_ZI_NEXT_DAY,
    year_boundary=YearBoundary.LUNAR_NEW_YEAR,
)


def compute(birth: BirthInput) -> tuple[dict[str, Any], str, list[str]]:
    warnings: list[str] = []
    solar_date: date = resolve_solar_date(birth)
    hour, minute = birth.resolved_hour_minute()
    if hour is None:
        raise EngineError("紫微斗数需要出生时辰，请至少选择时辰后再排盘")

    precision = TimePrecision.分 if birth.hour is not None else TimePrecision.时
    clock = time(hour, minute or 0)

    longitude: float | None = None
    timezone = BEIJING
    if birth.true_solar_time and birth.place is not None:
        longitude = birth.place.longitude
        warnings.append(f"已按真太阳时校正（经度 {longitude:.3f}°，由排盘库按天文算法换算）")
    elif birth.true_solar_time and birth.place is None:
        warnings.append("未提供出生地，未做真太阳时校正")

    if birth.place is not None:
        # 时区跟随出生地（UTC+9 → FixedOffset(+9h)），没有出生地才回落北京时间
        offset = timedelta(hours=birth.place.timezone)
        if offset != timedelta(hours=8):
            warnings.append(f"按出生地时区 {timezone_label(birth.place.timezone)} 起盘")
        timezone = FixedOffset(offset)

    record = GregorianBirthRecord(
        birth_date=solar_date,
        birth_time=clock,
        time_precision=precision,
        timezone=timezone,
        gender=Gender.男 if birth.gender == "male" else Gender.女,
        longitude_deg=longitude,
        place=birth.place.name if birth.place else None,
    )

    try:
        astrolabe = create_chart(record, CONFIG, sihua_variant=SihuaVariant.ZHONGYI999)
    except Exception as exc:  # noqa: BLE001 - 库抛的是通用异常
        raise EngineError(f"紫微排盘失败：{exc}") from exc

    chart = _serialize(astrolabe, birth, solar_date)
    return chart, "", warnings


def _serialize(astrolabe: Any, birth: BirthInput, solar_date: date) -> dict[str, Any]:
    readings = chart_brightness(astrolabe, table=BrightnessTable.QUANSHU_JUAN2)
    brightness = {
        (r.star.value, r.dizhi.value): (r.level.value if r.level is not None else None)
        for r in readings
    }

    sihua: dict[str, str] = {}
    for attr, label in HUA_NAMES.items():
        star = getattr(astrolabe.sihua, attr, None)
        if star is not None:
            sihua[star.value] = label

    stars_by_branch: dict[str, list[dict[str, Any]]] = {b: [] for b in BRANCH_ORDER}
    for placement in astrolabe.stars:
        branch = placement.dizhi.value
        stars_by_branch.setdefault(branch, []).append(
            {
                "name": placement.star.value,
                "kind": star_kind(placement.star.value),
                "brightness": brightness.get((placement.star.value, branch)),
                "sihua": sihua.get(placement.star.value),
            }
        )

    ming_branch = astrolabe.palaces[0].dizhi.value  # 命宫排第一
    shen_branch = astrolabe.shengong.value

    palaces: list[dict[str, Any]] = []
    for palace in astrolabe.palaces:
        branch = palace.dizhi.value
        stars = sorted(
            stars_by_branch.get(branch, []),
            key=lambda s: (s["kind"] != "major", s["name"]),
        )
        palaces.append(
            {
                "branch": branch,
                "stem": palace.tiangan.value,
                "name": PALACE_NAME_MODERN.get(palace.name.value, palace.name.value),
                "is_ming": branch == ming_branch,
                "is_shen": branch == shen_branch,
                "stars": stars,
            }
        )
    palaces.sort(key=lambda p: BRANCH_ORDER.index(p["branch"]))

    decades = [
        {
            "branch": d.dizhi.value,
            "palace": _palace_name_at(palaces, d.dizhi.value),
            "start_age": d.start_age,
            "end_age": d.end_age,
            "direction": d.direction.value,
        }
        for d in astrolabe.decades
    ]

    lunar_year = astrolabe.calculation.lunar_year
    current_age = datetime.now().year - lunar_year + 1
    current_decade = next(
        (d for d in decades if d["start_age"] <= current_age <= d["end_age"]), None
    )

    return {
        "engine": ENGINE_VERSION,
        "solar_date": solar_date.isoformat(),
        "lunar_date": solar_to_lunar_text(solar_date),
        "shichen": _shichen_of(birth),
        "gender": "男" if birth.gender == "male" else "女",
        "bureau": astrolabe.bureau.value,
        "ming_gong": ming_branch,
        "shen_gong": shen_branch,
        "sihua": {v: k for k, v in sihua.items()},
        "palaces": palaces,
        "decades": decades,
        "current_age": current_age,
        "current_decade": current_decade,
    }


def _palace_name_at(palaces: list[dict[str, Any]], branch: str) -> str:
    for p in palaces:
        if p["branch"] == branch:
            return p["name"]
    return ""


def _shichen_of(birth: BirthInput) -> str:
    from app.core.types import SHICHEN_HOURS

    if birth.shichen:
        return birth.shichen
    hour = birth.hour
    if hour is None:
        return "未知"
    for name, (start, _end) in SHICHEN_HOURS.items():
        if name == "子":
            continue
        if start <= hour < start + 2:
            return name
    return "子"
