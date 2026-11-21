"""八字领域的对外接口：SPEC + compute。"""

from __future__ import annotations

from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="bazi",
    name="四柱八字",
    tagline="以出生时刻排出年、月、日、时四柱，看十神格局与大运流年",
    name_en="Four Pillars (Bazi)",
    tagline_en="Cast the four pillars of year, month, day and hour from your birth moment, "
    "then read the Ten Gods, structure and luck cycles",
    requires_time=True,
    category="chart",
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput, options: dict | None = None) -> ChartEnvelope:
    chart, prompt_text, warnings = engine.compute(birth)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input=birth.model_dump(mode="json"),
        chart=chart,
        text=prompt_text or text.render(chart),
        warnings=warnings,
    )
