"""MBTI：SPEC + compute。"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, SystemSpec

from . import engine, text
from .constants import QUESTIONS

SPEC = SystemSpec(
    id="mbti",
    name="MBTI 测试",
    tagline="32 题五级量表，看四个维度的倾向与盲点",
    name_en="MBTI Test",
    tagline_en="32 five-point questions on your tendencies and blind spots across four dimensions",
    requires_birth=False,
    requires_time=False,
    category="fun",
    status="ready",
)


def render_text(chart: dict) -> str:
    return text.render(chart)


def compute(birth: BirthInput | None, options: dict[str, Any] | None = None) -> ChartEnvelope:
    chart = engine.compute(options)
    return ChartEnvelope(
        system=SPEC.id,
        engine_version=engine.ENGINE_VERSION,
        input={"question_count": len(QUESTIONS), "answered": chart["answered"]},
        chart=chart,
        text=text.render(chart),
        warnings=[chart["disclaimer"]],
    )
