"""把本命盘渲染成给 LLM 读的规范文本。"""

from __future__ import annotations

from typing import Any


def render(chart: dict[str, Any]) -> str:
    lines = ["# 西方占星本命盘", ""]
    lines.append(f"- 出生时刻（当地）：{chart.get('local_time', '')}（UTC{chart.get('timezone')}）")
    lines.append(f"- 换算 UTC：{chart.get('utc_time', '')}")
    if chart.get("place"):
        lines.append(f"- 出生地：{chart['place']}")
    lines.append(f"- 黄道：{chart.get('zodiac', '')}；分宫制：{chart.get('house_system', '')}")
    lines.append("")

    lines.append("## 三要素")
    for label, key in (("太阳", "sun"), ("月亮", "moon"), ("上升", "rising")):
        value = chart.get(key)
        if value:
            lines.append(f"- {label}：{value['sign']} {value['degree_in_sign']}°")
        else:
            lines.append(f"- {label}：不可用（缺少出生时刻或出生地）")
    lines.append("")

    lines.append("## 行星落座")
    lines.append("| 行星 | 星座 | 度数 | 宫位 | 逆行 |")
    lines.append("|---|---|---|---|---|")
    for planet in chart.get("planets", []):
        lines.append(
            f"| {planet['name']} | {planet['sign']} | {planet['degree_in_sign']}° | "
            f"{planet['house'] or '—'} | {'是' if planet['retrograde'] else ''} |"
        )
    lines.append("")

    fallback = chart.get("fallback")
    if fallback:
        lines.append("## 降级说明")
        lines.append(f"- {fallback}")
        lines.append("")
    else:
        if chart.get("aspects"):
            lines.append("## 主要相位")
            for aspect in chart["aspects"][:12]:
                lines.append(
                    f"- {aspect['a']} {aspect['type']} {aspect['b']}（{aspect['angle']}°，容许度 {aspect['orb']}°）"
                )
            lines.append("")

        balance = chart.get("balance")
        if balance:
            elements = "、".join(f"{k}{v}" for k, v in balance["elements"].items())
            modes = "、".join(f"{k}{v}" for k, v in balance["modes"].items())
            lines.append("## 元素与模式平衡（日月与内行星）")
            lines.append(f"- 元素：{elements}")
            lines.append(f"- 模式：{modes}")
            lines.append("")

    lines.append("> 以上为星历计算结果，解读时不得改写行星落座与相位。")
    return "\n".join(lines)
