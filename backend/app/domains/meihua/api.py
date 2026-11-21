"""梅花易数：SPEC + compute。

契约见 docs/ARCHITECTURE.md：本文件只导出 SPEC 与 compute()。
无需生辰，靠 options 起卦（time / number）。
"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, OptionField, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="meihua",
    name="梅花易数",
    tagline="以数起卦、以体用断事，看事情的本象、中变与落点",
    name_en="Meihua Yishu",
    tagline_en="Derive a hexagram from date or numbers and judge by body/use: the original image, "
    "the middle change and where it lands",
    requires_birth=False,
    requires_time=False,
    status="ready",
    category="divination",
    fields=[
        OptionField(
            key="method",
            label="起卦方式",
            kind="select",
            default="time",
            options=[
                {"value": "time", "label": "时间起卦", "label_en": "Cast by time"},
                {"value": "number", "label": "数字起卦", "label_en": "Cast by numbers"},
            ],
            hint="时间：按岁时起卦；数字：自己报两个数",
            label_en="Casting method",
            hint_en="Time: cast from date and hour; Numbers: two numbers you choose",
        ),
        OptionField(
            key="numbers",
            label="两个数字",
            kind="text",
            placeholder="如 37,18",
            hint="数字起卦用，逗号分隔",
            label_en="Two numbers",
            placeholder_en="e.g. 37,18",
            hint_en="For number casting, separated by commas",
        ),
        OptionField(
            key="date",
            label="日期",
            kind="date",
            hint="时间起卦用，留空按今天",
            label_en="Date",
            hint_en="For time casting; leave empty to use today",
        ),
        OptionField(
            key="hour",
            label="时辰",
            kind="number",
            placeholder="0-23",
            hint="时间起卦用，如 14",
            label_en="Hour",
            placeholder_en="0-23",
            hint_en="For time casting, e.g. 14",
        ),
    ],
)

AVAILABLE_METHODS: dict[str, dict[str, Any]] = {
    "time": {
        "name": "时间起卦",
        "description": "上卦=(年支序+农历月+农历日)%8，下卦=(再+时支序)%8，动爻=总和%6",
        "fields": ["date", "hour", "minute"],
    },
    "number": {
        "name": "数字起卦",
        "description": "上卦=第一数%8，下卦=第二数%8，动爻=(两数和)%6",
        "fields": ["numbers"],
    },
}


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput | None, options: dict[str, Any] | None = None) -> ChartEnvelope:
    chart = engine.compute(options)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input={
            "method": chart["method"],
            "cast_at": chart["cast_at"],
            "available_methods": AVAILABLE_METHODS,
        },
        chart=chart,
        text=text.render(chart),
        warnings=list(chart["warnings"]),
    )
