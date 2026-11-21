"""月运：SPEC + compute。"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, OptionField, SystemSpec
from app.domains.shared import fortune

SPEC = SystemSpec(
    id="monthly",
    name="月运",
    tagline="这个月的流月干支带来的主题与节奏",
    requires_birth=True,
    category="fortune",
    fields=[
        OptionField(
            key="date",
            label="月份",
            kind="date",
            hint="选该月任意一天即可，留空按本月计算",
        )
    ],
    status="ready",
)


def render_text(chart: dict) -> str:
    return fortune.render_text(chart)


def compute(birth: BirthInput, options: dict[str, Any] | None = None) -> ChartEnvelope:
    chart, warnings = fortune.compute(birth, options, period="month")
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=fortune.ENGINE_VERSION,
        input={"birth": birth.model_dump(mode="json"), "month": chart["label"]},
        chart=chart,
        text=fortune.render_text(chart),
        warnings=warnings,
    )
