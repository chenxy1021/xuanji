"""MBTI 计分：28 题 5 级量表，每个维度 7 题。"""

from __future__ import annotations

from typing import Any

from app.core.errors import EngineError

from .constants import DIMENSIONS, QUESTIONS, SCALE, TYPES

ENGINE_VERSION = "mbti-1.0"
POLE_MAX = 16  # 每个维度 8 题，每题最大偏移 ±2


def compute(options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    answers = options.get("answers")

    if not isinstance(answers, list) or len(answers) != len(QUESTIONS):
        raise EngineError(f"需要回答全部 {len(QUESTIONS)} 道题")

    values: list[int] = []
    for index, answer in enumerate(answers, start=1):
        if isinstance(answer, bool) or not isinstance(answer, int) or not 1 <= answer <= 5:
            raise EngineError(f"第 {index} 题的答案应为 1-5 的整数")
        values.append(answer)

    scores = {d["key"]: 0 for d in DIMENSIONS}
    for question, answer in zip(QUESTIONS, values, strict=True):
        delta = answer - 3
        dimension = next(d for d in DIMENSIONS if d["key"] == question["dim"])
        if question["pole"] == dimension["right"]:
            delta = -delta
        scores[question["dim"]] += delta

    details: list[dict[str, Any]] = []
    letters: list[str] = []
    for dimension in DIMENSIONS:
        score = scores[dimension["key"]]
        left_pct = round(50 + score / POLE_MAX * 50)
        left_pct = max(0, min(100, left_pct))
        pole = dimension["left"] if score >= 0 else dimension["right"]
        letters.append(pole)
        details.append(
            {
                "key": dimension["key"],
                "left": dimension["left"],
                "right": dimension["right"],
                "left_name": dimension["left_name"],
                "right_name": dimension["right_name"],
                "score": score,
                "left_pct": left_pct,
                "right_pct": 100 - left_pct,
                "dominant": dimension["left_name"] if score >= 0 else dimension["right_name"],
                "strength": _strength(abs(score)),
            }
        )

    mbti_type = "".join(letters)
    profile = TYPES[mbti_type]

    return {
        "engine": ENGINE_VERSION,
        "type": mbti_type,
        "name": profile["name"],
        "summary": profile["summary"],
        "strengths": profile["strengths"],
        "blind_spots": profile["blind_spots"],
        "fit": profile["fit"],
        "dimensions": details,
        "answered": len(values),
        "scale": SCALE,
        "disclaimer": "MBTI 是通俗性格分类，不是心理诊断，也不该用来给人贴标签或做招聘筛选。",
    }


def _strength(abs_score: int) -> str:
    if abs_score >= 8:
        return "明显"
    if abs_score >= 4:
        return "偏"
    return "轻微"
