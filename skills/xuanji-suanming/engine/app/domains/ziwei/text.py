"""把紫微命盘渲染成给 LLM 读的规范文本。"""

from __future__ import annotations

from typing import Any


def render(chart: dict[str, Any]) -> str:
    lines = ["# 紫微斗数命盘", ""]
    lines.append(f"- 公历：{chart.get('solar_date', '')}")
    lines.append(f"- 农历：{chart.get('lunar_date', '')}")
    lines.append(f"- 时辰：{chart.get('shichen', '')}")
    lines.append(f"- 性别：{chart.get('gender', '')}")
    lines.append(f"- 五行局：{chart.get('bureau', '')}")
    lines.append(f"- 命宫：{chart.get('ming_gong', '')}　身宫：{chart.get('shen_gong', '')}")
    lines.append("")

    lines.append("## 生年四化")
    for hua, star in (chart.get("sihua") or {}).items():
        lines.append(f"- {star}化{hua}")
    lines.append("")

    lines.append("## 十二宫")
    lines.append("| 宫位 | 地支 | 宫干 | 主星 | 辅煞杂曜 |")
    lines.append("|---|---|---|---|---|")
    for palace in chart.get("palaces", []):
        major = [f"{s['name']}（{s['brightness'] or '—'}）" for s in palace["stars"] if s["kind"] == "major"]
        others = [
            f"{s['name']}{'化' + s['sihua'] if s.get('sihua') else ''}"
            for s in palace["stars"]
            if s["kind"] != "major"
        ]
        mark = ""
        if palace.get("is_ming"):
            mark += "（命宫）"
        if palace.get("is_shen"):
            mark += "（身宫）"
        lines.append(
            f"| {palace['name']}{mark} | {palace['branch']} | {palace['stem']} | "
            f"{'、'.join(major) or '空宫'} | {'、'.join(others) or '—'} |"
        )
    lines.append("")

    if chart.get("decades"):
        lines.append("## 大限")
        for d in chart["decades"]:
            lines.append(
                f"- {d['start_age']}-{d['end_age']}岁（虚岁）{d['branch']}宫 {d['palace']}　{d['direction']}"
            )
        if chart.get("current_decade"):
            cd = chart["current_decade"]
            lines.append(f"- 当前虚岁 {chart.get('current_age')}，行 {cd['palace']} 大限")
        lines.append("")

    lines.append("> 以上为确定性排盘结果，解读时不得改写宫位、星曜与四化。")
    return "\n".join(lines)
