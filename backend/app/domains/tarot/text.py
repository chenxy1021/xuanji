"""把塔罗牌阵渲染成给 LLM 读的规范文本。"""

from __future__ import annotations

from typing import Any


def render(chart: dict[str, Any]) -> str:
    lines = ["# 塔罗牌阵", ""]
    lines.append(f"- 牌阵：{chart.get('spread_name', '')}（{chart.get('spread_description', '')}）")
    if chart.get("question"):
        lines.append(f"- 所问：{chart['question']}")
    lines.append("")
    lines.append("## 牌面")
    lines.append("| 位置 | 牌名 | 正逆 | 关键词 |")
    lines.append("|---|---|---|---|")
    for card in chart.get("cards", []):
        lines.append(
            f"| {card['position']} | {card['name']} | {card['orientation']} | {card['keywords']} |"
        )
    lines.append("")
    lines.append("> 牌面与正逆位由抽牌程序确定，解读时不得替换牌张。")
    return "\n".join(lines)
