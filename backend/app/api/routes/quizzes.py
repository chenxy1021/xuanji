"""量表类体系的题目接口。

`lang` 控制题干与量表标签的语言：`zh`（默认）保持原样，`en` 返回英文题干。
16 型名称与长解读暂只有中文，响应里的 `text_lang` 会标明当前文案语言。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.errors import AppError
from app.domains.mbti.constants import (
    DIMENSIONS,
    DIMENSIONS_EN,
    QUESTION_TEXT_EN,
    QUESTIONS,
    SCALE,
    SCALE_EN,
)

router = APIRouter(tags=["quizzes"])

SUPPORTED_LANGS = ("zh", "en")


def normalize_lang(raw: str | None) -> str:
    """把 `lang` 归一成受支持的语言代码；不认识的语言直接报错，不静默回退。"""
    if raw is None or not str(raw).strip():
        return "zh"
    code = str(raw).strip().lower().replace("_", "-")
    primary = code.split("-")[0]
    if primary in SUPPORTED_LANGS:
        return primary
    raise AppError("unsupported_lang", f"暂不支持该语言：{raw}（可选 zh / en）", status_code=422)


@router.get("/quizzes/mbti", summary="MBTI 题库")
def mbti_quiz(lang: str = "zh") -> dict[str, Any]:
    text_lang = normalize_lang(lang)
    if text_lang == "en":
        return {
            "id": "mbti",
            "name": "MBTI Test",
            "description": "32 questions, about 5 minutes. Answer on first instinct "
            "instead of weighing every option.",
            "scale": SCALE_EN,
            "dimensions": DIMENSIONS_EN,
            "questions": [
                {
                    "id": item["id"],
                    "dim": item["dim"],
                    "pole": item["pole"],
                    "text": QUESTION_TEXT_EN[item["id"]],
                }
                for item in QUESTIONS
            ],
            "text_lang": "en",
        }
    return {
        "id": "mbti",
        "name": "MBTI 测试",
        "description": "32 题，约 5 分钟。按第一反应作答，不用反复权衡。",
        "scale": SCALE,
        "dimensions": DIMENSIONS,
        "questions": QUESTIONS,
        "text_lang": "zh",
    }
