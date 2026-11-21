"""大六壬：SPEC + compute。"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, OptionField, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="daliuren",
    name="大六壬",
    tagline="月将加时起四课三传，看事情的起、承、转",
    requires_birth=False,
    requires_time=False,
    category="divination",
    fields=[
        OptionField(
            key="datetime",
            label="起课时刻",
            kind="datetime",
            placeholder="留空按当前时间",
            hint="大六壬以月将加时起课，同一时刻只能排出一课",
        )
    ],
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput | None, options: dict[str, Any] | None = None) -> ChartEnvelope:
    chart, warnings = engine.compute(birth, options)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input={"datetime": chart["datetime"], "day": chart["day_ganzhi"], "hour": chart["hour_ganzhi"]},
        chart=chart,
        text=text.render(chart),
        warnings=warnings,
    )
