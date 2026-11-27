"""西方占星：SPEC + compute。"""

from __future__ import annotations

from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="astrology",
    name="西方占星",
    tagline="太阳、月亮与上升，看性格底色与关系模式",
    name_en="Western Astrology",
    tagline_en="Sun, Moon and Ascendant: your underlying temperament and relationship patterns",
    requires_birth=True,
    requires_time=True,
    category="chart",
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput | None, options: dict | None = None) -> ChartEnvelope:
    if birth is None:
        from app.core.errors import AppError

        raise AppError("missing_birth", "西方占星需要出生信息", 422)
    chart, _, warnings = engine.compute(birth)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input=birth.model_dump(mode="json"),
        chart=chart,
        text=text.render(chart),
        warnings=warnings,
    )
