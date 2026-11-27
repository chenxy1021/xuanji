"""紫微斗数：SPEC + compute。"""

from __future__ import annotations

from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="ziwei",
    name="紫微斗数",
    tagline="十二宫、十四主星与四化，看人生各领域的主轴与变化",
    name_en="Zi Wei Dou Shu",
    tagline_en="Twelve palaces, fourteen major stars and the four transformations: "
    "the main axis and turning points of every life area",
    requires_time=True,
    category="chart",
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput, options: dict | None = None) -> ChartEnvelope:
    chart, _, warnings = engine.compute(birth)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input=birth.model_dump(mode="json"),
        chart=chart,
        text=text.render(chart),
        warnings=warnings,
    )
