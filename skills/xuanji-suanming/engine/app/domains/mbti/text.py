"""MBTI 结果 → 给 LLM 的规范文本。"""

from __future__ import annotations

from typing import Any


def render(chart: dict[str, Any]) -> str:
    lines = [
        f"# MBTI：{chart['type']}（{chart['name']}）",
        "",
        chart["summary"],
        "",
        "## 四个维度",
        "| 维度 | 倾向 | 比例 | 强度 |",
        "|---|---|---|---|",
    ]
    for d in chart["dimensions"]:
        lines.append(
            f"| {d['left_name']} / {d['right_name']} | {d['dominant']} | "
            f"{d['left']} {d['left_pct']}% / {d['right']} {d['right_pct']}% | {d['strength']} |"
        )
    lines.extend(
        [
            "",
            "## 优势",
            "、".join(chart["strengths"]),
            "",
            "## 盲点",
            "、".join(chart["blind_spots"]),
            "",
            f"## 适配环境\n{chart['fit']}",
            "",
            f"> {chart['disclaimer']}",
        ]
    )
    return "\n".join(lines)
