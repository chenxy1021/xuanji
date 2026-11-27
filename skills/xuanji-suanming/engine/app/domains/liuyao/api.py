"""六爻纳甲：SPEC + compute。

契约见 docs/ARCHITECTURE.md：本文件只导出 SPEC 与 compute()。
无需生辰，靠 options 起卦（coins / time / number）。
"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="liuyao",
    name="六爻纳甲",
    tagline="针对具体问题起卦，看世应、六亲与动变",
    name_en="Liu Yao (Six Lines)",
    tagline_en="Cast a hexagram for one specific question and read the host/guest lines, "
    "six relatives and moving lines",
    requires_birth=False,
    requires_time=False,
    category="divination",
    status="ready",
)

AVAILABLE_METHODS: dict[str, dict[str, Any]] = {
    "coins": {
        "name": "铜钱摇卦",
        "description": "摇六次，自下而上记录 6/7/8/9（6 老阴、7 少阳、8 少阴、9 老阳）",
        "fields": ["lines"],
    },
    "time": {
        "name": "时间起卦",
        "description": "以年月日时起卦（梅花易数法）",
        "fields": ["date", "hour", "minute"],
    },
    "number": {
        "name": "数字起卦",
        "description": "报两个正整数，以数取卦与动爻",
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
            "question": chart["question"],
            "cast_at": chart["cast_at"],
            "available_methods": {
                key: {
                    "name": spec["name"],
                    "description": spec["description"],
                    "fields": spec["fields"],
                }
                for key, spec in AVAILABLE_METHODS.items()
            },
        },
        chart=chart,
        text=text.render(chart),
        warnings=list(chart["warnings"]),
    )
