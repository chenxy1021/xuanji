"""紫微合盘：SPEC + compute。

需要两份生辰：payload.birth 为甲方，payload.secondary 为乙方。
"""

from __future__ import annotations

from typing import Any

from app.core.errors import EngineError
from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="ziwei_hepan",
    name="紫微合盘",
    tagline="两张紫微盘互看：命宫、夫妻宫与四化飞入",
    name_en="Ziwei Synastry",
    tagline_en="Two ziwei charts read against each other: life palace, spouse palace "
    "and flying transformations",
    requires_birth=True,
    requires_secondary=True,
    category="synastry",
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput, options: dict[str, Any] | None = None) -> ChartEnvelope:
    options = options or {}
    secondary = options.get("secondary")
    if secondary is None:
        raise EngineError("紫微合盘需要第二个人的出生信息")
    secondary = BirthInput.model_validate(secondary)

    chart, prompt_text, warnings = engine.compute(birth, secondary)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input={"a": birth.model_dump(mode="json"), "b": secondary.model_dump(mode="json")},
        chart=chart,
        text=prompt_text or text.render(chart),
        warnings=warnings,
    )
