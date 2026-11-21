"""孔明神卦 → 给 LLM 的规范文本。"""

from __future__ import annotations

from typing import Any


def render(chart: dict[str, Any]) -> str:
    lot = chart["lot"]
    calc = chart["calculation"]
    reading = chart["reading"]
    lines = ["# 孔明神卦（诸葛神数）", ""]
    if chart.get("question"):
        lines.append(f"- 所问：{chart['question']}")
    lines.append(f"- 报字：{'、'.join(chart['characters'])}")
    lines.append(f"- 取画：{calc['detail']}")
    lines.append(f"- 签号：第 {lot['number']} 签（{lot['fortune']}）")
    lines.append(
        f"- 卦爻：{lot['palace']}　{lot['hexagram']}变{lot['changed']}（{lot['line']}）"
    )
    lines.append("")
    lines.append("## 签文")
    lines.append("")
    lines.append(lot["poem"])
    lines.append("")
    lines.append("## 断语")
    lines.append("")
    lines.append(f"- 基调：{reading['tone']}（{'、'.join(reading['keywords'])}）")
    lines.append(f"- 提示：{reading['advice']}")
    lines.append("")
    lines.append("## 解读提示")
    lines.append("")
    lines.append("- 签文是断事的骨架，先逐句落到所问之事上，再给结论与可执行的建议。")
    lines.append("- 只依据签号、签级、卦爻与签文展开，不得改动签文，也不要另起一卦。")
    lines.append("- 若所问为空，按「近期整体运势」解读，并提醒用户一次只问一事。")
    lines.append(f"- {chart['disclaimer']}")
    lines.append("")
    return "\n".join(lines)
