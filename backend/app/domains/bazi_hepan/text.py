"""八字合盘 → 给 LLM 的规范文本。"""

from __future__ import annotations

from typing import Any


def _person_block(title: str, p: dict[str, Any]) -> list[str]:
    pillars = p["pillars"]
    lines = [
        f"## {title}",
        f"- 公历：{p['solar_date']}　农历：{p['lunar_date']}　{p['shichen']}",
        f"- 四柱：{' '.join(pillars[k] for k in ('year', 'month', 'day', 'hour'))}",
        f"- 日主：{p['day_master']}（{p['day_master_element']}）",
        f"- 生肖：{p['zodiac']}　夫妻宫（日支）：{p['spouse_palace']}",
        "- 五行分布：" + "　".join(f"{k}{v}%" for k, v in p["wuxing"].items()),
    ]
    if p["missing"]:
        lines.append(f"- 所缺五行：{'、'.join(p['missing'])}")
    return lines


def render(chart: dict[str, Any]) -> str:
    lines = ["# 八字合盘", ""]
    lines.extend(_person_block("甲方", chart["a"]))
    lines.append("")
    lines.extend(_person_block("乙方", chart["b"]))
    lines.append("")

    lines.append("## 两盘关系")
    lines.append("| 范围 | 关系 | 说明 |")
    lines.append("|---|---|---|")
    for m in chart.get("matches", []):
        lines.append(f"| {m['scope']} | {m['kind']} | {m['detail']} |")
    lines.append("")

    if chart.get("complement"):
        lines.append("## 五行互补")
        for c in chart["complement"]:
            lines.append(f"- {c['detail']}")
        lines.append("")

    lines.append("## 综合")
    lines.append(f"- 参考分：{chart['score']}/100（{chart['level']}）")
    for tip in chart.get("advice", []):
        lines.append(f"- {tip}")
    lines.append("")
    lines.append(f"> {chart.get('disclaimer', '')}")
    return "\n".join(lines)
