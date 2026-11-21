"""把小六壬课盘渲染成给 LLM 读的规范文本。"""

from __future__ import annotations

from typing import Any


def render(chart: dict[str, Any]) -> str:
    lines: list[str] = ["# 小六壬", ""]
    lines.append(f"- 起课方式：{chart.get('method_name', chart.get('method', ''))}")
    lines.append(f"- 起课时刻：{chart.get('cast_at', '')}（{chart.get('lunar', {}).get('text', '')}）")
    if chart.get("cast", {}).get("basis"):
        lines.append(f"- 起课依据：{chart['cast']['basis']}")
    lines.append("")

    lines.append("## 三宫")
    lines.append("")
    lines.append("| 宫位 | 含义 | 落宫 | 五行 | 方位 | 神将 | 吉凶 |")
    lines.append("|---|---|---|---|---|---|---|")
    for palace in chart.get("palaces", []):
        lines.append(
            f"| {palace['role']} | {palace['role_meaning']} | {palace['name']} | {palace['element']} "
            f"| {palace['direction']} | {palace['deity']} | {palace['luck']} |"
        )
    lines.append("")

    for palace in chart.get("palaces", []):
        lines.append(f"### {palace['role']}：{palace['name']}（{palace['luck']}）")
        lines.append("")
        lines.append(f"- {palace['role_desc']}")
        lines.append(f"- 象意：{palace['omen']}")
        lines.append(f"- 断法：{palace['advice']}")
        lines.append("")

    main = chart.get("main") or {}
    if main:
        lines.append(f"## 断事以时宫为主：{main.get('name', '')}（{main.get('luck', '')}）")
        lines.append("")
        lines.append(chart.get("summary", ""))
        lines.append("")

    lines.append("## 断课提示")
    lines.append("")
    lines.append("- 三宫看的是同一条事情的起因、过程与结果：月宫看天时，日宫看推进，时宫看落点。")
    lines.append("- 只依据上表落宫与吉凶推断，不得改动宫名、五行、方位与吉凶。")
    for warning in chart.get("warnings") or []:
        lines.append(f"- 注意：{warning}")
    lines.append("")
    return "\n".join(lines)
