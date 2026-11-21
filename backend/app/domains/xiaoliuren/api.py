"""小六壬：SPEC + compute。

契约见 docs/ARCHITECTURE.md：本文件只导出 SPEC 与 compute()。
无需生辰，靠 options 起课（time / number / random）。
"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, OptionField, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="xiaoliuren",
    name="小六壬",
    tagline="掐指一算，六宫定吉凶，看事情的起因、过程与结局",
    requires_birth=False,
    requires_time=False,
    status="ready",
    category="divination",
    fields=[
        OptionField(
            key="method",
            label="起课方式",
            kind="select",
            default="random",
            options=[
                {"value": "random", "label": "随机起课"},
                {"value": "time", "label": "时间起课"},
                {"value": "number", "label": "数字起课"},
            ],
            hint="随机：直接摇课；时间：按当前或指定时刻顺数；数字：自己报三个数",
        ),
        OptionField(key="numbers", label="三个数字", kind="text", placeholder="如 3,8,5", hint="数字起课用，逗号分隔"),
        OptionField(key="date", label="日期", kind="date", hint="时间起课用，留空按今天"),
        OptionField(key="hour", label="时辰", kind="number", placeholder="0-23", hint="时间起课用，如 14"),
    ],
)

AVAILABLE_METHODS: dict[str, dict[str, Any]] = {
    "random": {"name": "随机起课", "description": "服务端随机取三宫", "fields": []},
    "time": {
        "name": "时间起课",
        "description": "按农历月日时辰从大安顺数，得月宫、日宫、时宫",
        "fields": ["date", "hour", "minute"],
    },
    "number": {
        "name": "数字起课",
        "description": "报三个正整数，分别定月宫、日宫、时宫（n % 6 取宫）",
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
