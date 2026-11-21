"""奇门终身局：SPEC + compute。"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="qimen",
    name="奇门终身局",
    tagline="以出生时刻起局，看年命、日干、时干三宫的一生格局",
    name_en="Qi Men Lifelong Chart",
    tagline_en="Cast a chart from your birth moment and read the three palaces of year-life, "
    "day stem and hour stem across a whole life",
    requires_birth=True,
    requires_time=True,
    category="chart",
    fields=[],
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput | None, options: dict[str, Any] | None = None) -> ChartEnvelope:
    chart, warnings = engine.compute(birth, options)
    lifelong = chart["lifelong"]
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input={
            "datetime": chart["datetime"],
            "four_pillars": chart["four_pillars"],
            "ju": chart["ju"],
            "dun": chart["dun"],
            "anchors": [
                {
                    "key": a["key"],
                    "label": a["label"],
                    "ganzhi": a["ganzhi"],
                    "palace": a["palace"]["number"] if a["palace"] else None,
                }
                for a in lifelong["anchors"]
            ],
        },
        chart=chart,
        text=text.render(chart),
        warnings=warnings,
    )
