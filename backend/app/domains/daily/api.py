"""日运：SPEC + compute。"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, OptionField, SystemSpec
from app.domains.shared import fortune

SPEC = SystemSpec(
    id="daily",
    name="日运",
    tagline="今天的干支与你的命局是什么关系",
    requires_birth=True,
    category="fortune",
    fields=[
        OptionField(
            key="date",
            label="日期",
            kind="date",
            hint="留空按今天计算",
        )
    ],
    status="ready",
)


def render_text(chart: dict) -> str:
    return fortune.render_text(chart)


def compute(birth: BirthInput, options: dict[str, Any] | None = None) -> ChartEnvelope:
    chart, warnings = fortune.compute(birth, options, period="day")
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=fortune.ENGINE_VERSION,
        input={"birth": birth.model_dump(mode="json"), "date": chart["date"]},
        chart=chart,
        text=fortune.render_text(chart),
        warnings=warnings,
    )
