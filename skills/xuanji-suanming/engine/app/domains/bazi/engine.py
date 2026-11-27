"""八字排盘引擎适配层。

核心算法来自 MIT 许可的 bazi-skill（https://github.com/jinchenma94/bazi-skill），
已 vendored 为 `_vendor_pai_pan.py`，原样保留以降低回归风险。
本文件只负责：统一入参 → 真太阳时校正 → 调用 → 规整出 canonical JSON。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.errors import EngineError
from app.core.types import BirthInput
from app.domains.shared.calendar import resolve_solar_date, solar_to_lunar_text
from app.domains.shared.solar_time import (
    solar_time_info,
    standard_meridian_for,
    timezone_label,
    to_true_solar_time,
)

from . import _vendor_pai_pan as pp

GENDER_MAP = {"male": "男", "female": "女"}
ENGINE_VERSION = "bazi-1.0"
_LIUNIAN_WINDOW = 12


def compute(birth: BirthInput) -> tuple[dict[str, Any], str, list[str]]:
    """返回 (chart, prompt_text, warnings)。"""
    warnings: list[str] = []
    solar_date = resolve_solar_date(birth)
    hour, minute = birth.resolved_hour_minute()

    tst_info: dict[str, Any] | None = None
    if birth.true_solar_time and birth.place is not None and hour is not None:
        clock = datetime(solar_date.year, solar_date.month, solar_date.day, hour, minute or 0)
        # 标准子午线按出生地时区推（UTC+9 → 135°E），否则国外出生会按北京时间偏 1 小时
        meridian = standard_meridian_for(birth.place.timezone)
        true_dt = to_true_solar_time(clock, birth.place.longitude, meridian)
        tst_info = solar_time_info(clock, birth.place.longitude, meridian)
        if true_dt.date() != solar_date:
            warnings.append("真太阳时校正后跨越日界，日柱按校正后日期计算")
        solar_date = true_dt.date()
        hour, minute = true_dt.hour, true_dt.minute
        warnings.append(
            f"已按真太阳时校正（按 {timezone_label(birth.place.timezone)} 标准时 + 经度差 + 均时差，"
            f"经度 {birth.place.longitude:.3f}°、基准子午线 {meridian:.1f}°，"
            f"合计 {tst_info['total_correction_minutes']} 分钟）"
        )
    elif birth.true_solar_time and birth.place is None:
        warnings.append("未提供出生地，未做真太阳时校正")

    lunar_text = solar_to_lunar_text(solar_date)

    try:
        raw = pp.compute(
            solar_date,
            hour=hour,
            minute=minute,
            sex=GENDER_MAP[birth.gender],
            place=birth.place.name if birth.place else None,
            lunar_display=lunar_text,
        )
    except Exception as exc:  # noqa: BLE001
        raise EngineError(f"八字排盘失败：{exc}") from exc

    warnings.extend(w for w in raw.get("warnings", []) if w not in warnings)
    chart = _serialize(raw, birth, tst_info)
    text = pp.format_report(raw)
    return chart, text, warnings


def _serialize(raw: dict[str, Any], birth: BirthInput, tst_info: dict[str, Any] | None) -> dict[str, Any]:
    pillars = {
        key: {"gan": gan, "zhi": zhi, "shishen": shishen, "canggan": canggan}
        for key, (gan, zhi, shishen, canggan) in raw["pillars"].items()
    }

    dayun = [
        {"index": step, "age_range": span, "ganzhi": gz}
        for step, span, gz in raw.get("dayun_rows", [])
    ]

    # 流年只保留最近若干年，避免响应过大
    years = raw.get("liunian_years") or []
    recent_years = years[-_LIUNIAN_WINDOW:]
    liunian = [{"year": y, "ganzhi": pp.liunian_gz(y)} for y in recent_years]

    return {
        "engine": ENGINE_VERSION,
        "solar_date": raw["solar_text"],
        "lunar_date": raw["lunar_text"],
        "shichen": raw["shichen_text"],
        "gender": GENDER_MAP[birth.gender],
        "zishi": raw["zishi"],
        "pillars": pillars,
        "forward": raw["forward"],
        "qiyun": raw["qiyun_text"],
        "dayun": dayun,
        "liunian": liunian,
        "shensha": raw.get("shensha_lines", []),
        "jie": raw.get("jie_name"),
        "true_solar_time": tst_info,
    }
