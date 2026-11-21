"""塔罗牌：SPEC + compute。"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text
from .deck import SPREADS

SPEC = SystemSpec(
    id="tarot",
    name="塔罗牌",
    tagline="抽牌看当下的处境、阻力与建议",
    name_en="Tarot",
    tagline_en="Draw cards for the situation at hand, what blocks it and what to do next",
    requires_birth=False,
    requires_time=False,
    category="divination",
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput | None, options: dict[str, Any] | None = None) -> ChartEnvelope:
    chart = engine.compute(options)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input={
            "spread": chart["spread"],
            "question": chart["question"],
            "available_spreads": {
                key: {"name": spec["name"], "description": spec["description"], "count": len(spec["positions"])}
                for key, spec in SPREADS.items()
            },
        },
        chart=chart,
        text=text.render(chart),
        warnings=[],
    )
