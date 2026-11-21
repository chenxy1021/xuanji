"""把梅花易数卦盘渲染成给 LLM 读的规范文本。"""

from __future__ import annotations

from typing import Any


def _gua_block(label: str, gua: dict[str, Any]) -> list[str]:
    lines = [
        f"### {label}：{gua['name']} {gua['symbol']}",
        "",
        f"- 上下卦：上{gua['upper']}{gua['upper_symbol']}（{gua['upper_element']}） "
        f"下{gua['lower']}{gua['lower_symbol']}（{gua['lower_element']}）",
        f"- 象意：{gua['yixiang']}",
        "",
    ]
    return lines


def render(chart: dict[str, Any]) -> str:
    lines: list[str] = ["# 梅花易数", ""]
    lines.append(f"- 起卦方式：{chart.get('method_name', chart.get('method', ''))}")
    lines.append(f"- 起卦时刻：{chart.get('cast_at', '')}")
    lunar = chart.get("lunar") or {}
    if lunar:
        leap = "闰" if lunar.get("is_leap_month") else ""
        lines.append(
            f"- 起卦依据：{lunar.get('year_ganzhi', '')}年 农历{leap}{lunar.get('month', '')}月"
            f"{lunar.get('day', '')}日{lunar.get('shichen', '')}时"
        )
    if chart.get("cast", {}).get("detail"):
        lines.append(f"- 算数过程：{chart['cast']['detail']}")
    lines.append("")

    lines.extend(_gua_block("本卦", chart["ben"]))
    lines.extend(_gua_block("互卦", chart["hu"]))
    lines.extend(_gua_block("变卦", chart["bian"]))

    ti_yong = chart.get("ti_yong") or {}
    ti = ti_yong.get("ti") or {}
    yong = ti_yong.get("yong") or {}
    relation = chart.get("relation") or {}
    lines.append(f"## 体用：动在{chart.get('moving_line_name', '')}")
    lines.append("")
    lines.append(
        f"- 体卦：{ti.get('position', '')}{ti.get('trigram', '')}（{ti.get('element', '')}）；"
        f"用卦：{yong.get('position', '')}{yong.get('trigram', '')}（{yong.get('element', '')}）"
    )
    lines.append(f"- 生克：{relation.get('name', '')}，判为「{relation.get('result', '')}」——{relation.get('explain', '')}")
    lines.append("")

    lines.append("## 总断")
    lines.append("")
    lines.append(chart.get("judgement", ""))
    lines.append("")

    lines.append("## 断卦提示")
    lines.append("")
    lines.append("- 体卦代表求测者自身，用卦代表所问之事；断吉凶以体用生克为主，本卦、互卦、变卦看事情的起、中、终。")
    lines.append("- 只依据上表卦象、象意与体用生克推断，不得改动卦名、动爻与生克结论。")
    for warning in chart.get("warnings") or []:
        lines.append(f"- 注意：{warning}")
    lines.append("")
    return "\n".join(lines)
