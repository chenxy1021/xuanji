"""把八字 chart JSON 渲染成给 LLM 读的规范文本。"""

from __future__ import annotations

from typing import Any

_PILLAR_LABELS = [("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")]


def render(chart: dict[str, Any]) -> str:
    lines: list[str] = ["# 四柱八字命盘", ""]
    lines.append(f"- 公历：{chart.get('solar_date', '')}")
    lines.append(f"- 农历：{chart.get('lunar_date', '')}")
    lines.append(f"- 时辰：{chart.get('shichen', '')}")
    lines.append(f"- 性别：{chart.get('gender', '')}")
    if chart.get("true_solar_time"):
        tst = chart["true_solar_time"]
        lines.append(
            f"- 真太阳时：校正 {tst['total_correction_minutes']} 分钟 → {tst['true_solar_time']}"
        )
    lines.append("")

    lines.append("## 四柱")
    for key, label in _PILLAR_LABELS:
        p = chart.get("pillars", {}).get(key)
        if not p:
            continue
        lines.append(
            f"- {label}：{p['gan']}{p['zhi']}（十神：{p['shishen']}；藏干：{p['canggan']}）"
        )
    lines.append("")

    if chart.get("shensha"):
        lines.append("## 神煞")
        lines.extend(f"- {line}" for line in chart["shensha"])
        lines.append("")

    lines.append(f"## 大运（{chart.get('qiyun', '')}起运，{'顺' if chart.get('forward') else '逆'}行）")
    for row in chart.get("dayun", []):
        lines.append(f"- 第{row['index']}步 {row['age_range']}：{row['ganzhi']}")
    lines.append("")

    if chart.get("liunian"):
        lines.append("## 近年流年")
        for row in chart["liunian"]:
            lines.append(f"- {row['year']}年：{row['ganzhi']}")
        lines.append("")

    lines.append("> 以上为确定性排盘结果，解读时不得改写干支、神煞与大运。")
    return "\n".join(lines)
