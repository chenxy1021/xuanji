"""大六壬适配层。

排盘规则来自 MIT 许可的 `kinliuren`（https://github.com/kentang2017/kinliuren），
本文件负责：解析时刻 → 农历/节气/干支 → 调用 → 中文 canonical JSON。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from kinliuren.kinliuren import Liuren
from lunar_python import Solar

from app.core.errors import EngineError
from app.core.types import BirthInput

from .constants import (
    MONTH_GENERAL,
    general,
    liuqin,
    pattern,
    void_branches,
    xun_of,
)

ENGINE_VERSION = "daliuren-0.1.2"
METHOD_LABEL = "大六壬·月将加时"


def compute(
    birth: BirthInput | None, options: dict[str, Any] | None = None
) -> tuple[dict[str, Any], list[str]]:
    from app.domains.shared.moment import resolve_moment

    moment, warnings = resolve_moment(birth, options)

    lunar = Solar.fromYmdHms(
        moment.year, moment.month, moment.day, moment.hour, moment.minute, 0
    ).getLunar()
    jieqi = lunar.getPrevJieQi().getName()
    month_text = lunar.getMonthInChinese()
    day_gz = lunar.getDayInGanZhi()
    hour_gz = lunar.getTimeInGanZhi()

    lunar_month = month_text.lstrip("闰")
    if lunar_month != month_text:
        warnings.append("起课时刻处于闰月，月将仍按节气推算")

    nobleman = 0 if hour_gz[1] in "卯辰巳午未申" else 1

    try:
        raw = Liuren(jieqi, lunar_month, day_gz, hour_gz).result(nobleman)
    except Exception as exc:  # noqa: BLE001 - 上游库抛通用异常
        raise EngineError(f"大六壬排课失败：{exc}") from exc

    return _serialize(raw, moment, lunar_month, day_gz, hour_gz, nobleman), warnings


def _serialize(
    raw: dict[str, Any],
    moment: datetime,
    lunar_month: str,
    day_gz: str,
    hour_gz: str,
    nobleman: int,
) -> dict[str, Any]:
    earth_to_heaven: dict[str, str] = raw["地轉天盤"]
    earth_to_general: dict[str, str] = raw["地轉天將"]

    month_general_branch = earth_to_heaven.get(hour_gz[1], "")
    void = void_branches(day_gz)

    three = []
    for label in ("初傳", "中傳", "末傳"):
        branch, gen, kin, dungan = raw["三傳"][label]
        three.append(
            {
                "stage": label.replace("傳", "传"),
                "branch": branch,
                "general": general(gen),
                "liuqin": liuqin(kin),
                "hidden_stem": dungan,
                "void": branch in void,
            }
        )

    lessons = []
    for label, index in (("一課", 1), ("二課", 2), ("三課", 3), ("四課", 4)):
        pair, gen = raw["四課"][label]
        lessons.append(
            {
                "index": index,
                "upper": pair[0],
                "lower": pair[1],
                "general": general(gen),
            }
        )

    plates = [
        {
            "earth": earth,
            "heaven": earth_to_heaven[earth],
            "general": general(earth_to_general[earth]),
        }
        for earth in earth_to_heaven
    ]

    patterns: list[str] = []
    for raw_pattern in raw["格局"]:
        name = pattern(raw_pattern)
        if name in {"不適用，或試他法", "不适用，或试他法"} or name in patterns:
            continue
        patterns.append(name)

    return {
        "engine": ENGINE_VERSION,
        "pattern": patterns,
        "method": METHOD_LABEL,
        "datetime": moment.strftime("%Y-%m-%d %H:%M"),
        "jieqi": raw["節氣"],
        "lunar_month": lunar_month,
        "day_ganzhi": day_gz,
        "hour_ganzhi": hour_gz,
        "xun": xun_of(day_gz),
        "void_branches": void,
        "month_general": {
            "branch": month_general_branch,
            "name": MONTH_GENERAL.get(month_general_branch, ""),
        },
        "day_horse": raw["日馬"],
        "four_lessons": lessons,
        "three_transmissions": three,
        "plates": plates,
        "nobleman": "昼贵" if nobleman == 0 else "夜贵",
    }
