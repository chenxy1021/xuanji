"""紫微合盘 → 给 LLM 的规范文本。"""

from __future__ import annotations

from typing import Any


def _person_block(title: str, p: dict[str, Any]) -> list[str]:
    return [
        f"## {title}",
        f"- 公历：{p['solar_date']}　农历：{p['lunar_date']}　{p['shichen']}",
        f"- 五行局：{p['bureau']}　命宫：{p['ming_branch']}　身宫：{p['shen_branch']}",
        f"- 命宫主星：{'、'.join(p['ming_stars']) or '空宫'}",
        f"- 夫妻宫：{p['spouse_branch']}　主星：{'、'.join(p['spouse_stars']) or '空宫'}",
        f"- 福德宫：{p['fude_branch']}　主星：{'、'.join(p['fude_stars']) or '空宫'}",
        "- 生年四化：" + "　".join(f"{star}化{hua}" for hua, star in p["sihua"].items()),
    ]


def render(chart: dict[str, Any]) -> str:
    lines = ["# 紫微合盘", ""]
    lines.extend(_person_block("甲方", chart["a"]))
    lines.append("")
    lines.extend(_person_block("乙方", chart["b"]))
    lines.append("")

    lines.append("## 宫位与星曜呼应")
    lines.append("| 范围 | 类型 | 说明 |")
    lines.append("|---|---|---|")
    for m in chart.get("matches", []):
        lines.append(f"| {m['scope']} | {m['kind']} | {m['detail']} |")
    lines.append("")

    lines.append("## 综合")
    lines.append(f"- 参考分：{chart['score']}/100（{chart['level']}）")
    for tip in chart.get("advice", []):
        lines.append(f"- {tip}")
    lines.append("")
    lines.append(f"> {chart.get('disclaimer', '')}")
    return "\n".join(lines)
