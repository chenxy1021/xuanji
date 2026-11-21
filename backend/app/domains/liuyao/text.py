"""把六爻卦盘渲染成给 LLM 读的规范文本。"""

from __future__ import annotations

from typing import Any

from . import constants as C

_POSITION_NAMES = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}


def _line_glyph(line: dict[str, Any]) -> str:
    """阳爻实线、阴爻断线；动爻标 ○（老阳）/ ✕（老阴）。"""
    if line["yinyang"] == "阳":
        glyph = "▅▅▅▅▅"
        mark = "○" if line["moving"] else " "
    else:
        glyph = "▅▅　▅▅"
        mark = "✕" if line["moving"] else " "
    return f"{glyph} {mark}"


def _gua_table(gua: dict[str, Any], label: str) -> list[str]:
    title = (
        f"## {label}：{gua['full_name']} {gua['symbol']}　"
        f"{gua['palace']}宫{gua['stage']}（宫五行属{gua['element']}）"
    )
    lines = [title, ""]
    lines.append("| 爻位 | 六神 | 六亲 | 卦画 | 纳甲 | 世应 |")
    lines.append("|---|---|---|---|---|---|")
    for line in reversed(gua["lines"]):
        lines.append(
            f"| {_POSITION_NAMES[line['position']]} | {line['liushen']} | {line['liuqin']} "
            f"| {_line_glyph(line)} | {line['gan_zhi']}{line['wuxing']} | {line['shi_ying'] or ''} |"
        )
    lines.append("")
    lines.append(
        f"> 世在{_POSITION_NAMES[gua['shi_line']]}，应在{_POSITION_NAMES[gua['ying_line']]}；"
        f"上卦{_trigram_label(gua['upper'])}，下卦{_trigram_label(gua['lower'])}。"
        f"六亲以本宫（{gua['palace']}宫，属{gua['element']}）五行论生克。"
    )
    lines.append("")
    return lines


def _trigram_label(name: str) -> str:
    info = C.TRIGRAMS[name]
    return f"{name}{info['symbol']}（{info['nature']}，属{info['element']}）"


def render(chart: dict[str, Any]) -> str:
    lines: list[str] = ["# 六爻纳甲", ""]
    lines.append(f"- 起卦方式：{chart.get('method_name', chart.get('method', ''))}")
    if chart.get("question"):
        lines.append(f"- 所问：{chart['question']}")
    lines.append(f"- 起卦时刻：{chart.get('cast_at', '')}（{chart.get('lunar_date', '')}）")
    lines.append(
        f"- 年月日：{chart.get('year_gan_zhi', '')}年 {chart.get('month_gan_zhi', '')}月 "
        f"{chart.get('day_gan_zhi', '')}日"
    )
    moving = chart.get("moving_lines") or []
    if moving:
        lines.append("- 动爻：" + "、".join(_POSITION_NAMES[position] for position in moving))
    else:
        lines.append("- 动爻：无（六爻皆静）")
    lines.append("")
    lines.extend(_gua_table(chart["ben_gua"], "本卦"))

    if chart.get("bian_gua"):
        lines.extend(_gua_table(chart["bian_gua"], "变卦"))

    if chart.get("hu_gua"):
        lines.extend(_gua_table(chart["hu_gua"], "互卦"))

    lines.append("## 断卦提示")
    lines.append("")
    lines.append("- 六神由日干起青龙，自初爻向上依次排列；动爻为老阳（9）与老阴（6），变卦中阴阳取反。")
    lines.append("- 六亲以各卦自身卦宫五行为基准：生我者父母，我生者子孙，克我者官鬼，我克者妻财，同我者兄弟。")
    lines.append("- 只依据上表卦象、纳甲、六亲六神与世应关系推断，不得改动卦名、动爻与干支。")
    for warning in chart.get("warnings") or []:
        lines.append(f"- 注意：{warning}")
    lines.append("")
    return "\n".join(lines)
