"""孔明神卦：SPEC + compute。"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput, ChartEnvelope, OptionField, SystemSpec

from . import engine, text

SPEC = SystemSpec(
    id="kongming",
    name="孔明神卦",
    tagline="诸葛神数：写下三个字，按康熙笔画取 384 签之一",
    name_en="Kongming Oracle",
    tagline_en="Zhuge's divine numbers: write three characters and draw one of 384 slips by Kangxi stroke count",
    requires_birth=False,
    requires_time=False,
    category="divination",
    fields=[
        OptionField(
            key="question",
            label="所问之事",
            kind="textarea",
            placeholder="一次只问一件事，如：这份工作要不要接？",
            label_en="Your question",
            placeholder_en="Ask about one thing only, e.g. should I take this job?",
            hint_en="One question per cast — the slip answers what you hold in mind",
        ),
        OptionField(
            key="characters",
            label="写三个字",
            kind="text",
            required=True,
            placeholder="如：佑咱统",
            hint="心中默念所问之事，随手写三个汉字；简体按常用繁体折算笔画",
            label_en="Three characters",
            placeholder_en="e.g. 佑咱统",
            hint_en="Keep your question in mind and write three Chinese characters; "
            "simplified forms are counted by their common traditional strokes",
        ),
    ],
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
            "characters": "".join(chart["characters"]),
            "question": chart["question"],
            "number": chart["lot"]["number"],
        },
        chart=chart,
        text=text.render(chart),
        warnings=list(chart["warnings"]),
    )
