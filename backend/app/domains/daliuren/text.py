"""大六壬课盘 → 给 LLM 的规范文本。"""

from __future__ import annotations

from typing import Any


def render(chart: dict[str, Any]) -> str:
    lines = [
        "# 大六壬",
        "",
        f"- 起课：{chart['datetime']}",
        f"- 节气：{chart['jieqi']}　农历：{chart['lunar_month']}月",
        f"- 日干支：{chart['day_ganzhi']}（{chart['xun']}旬，"
        f"空亡 {'、'.join(chart['void_branches'])}）",
        f"- 时干支：{chart['hour_ganzhi']}（{chart['nobleman']}）",
        f"- 月将：{chart['month_general']['branch']}（{chart['month_general']['name']}）",
        f"- 日马：{chart['day_horse']}",
        f"- 课体：{'、'.join(chart['pattern'])}",
        "",
        "## 四课",
        "| 课 | 上神 | 下神 | 天将 |",
        "|---|---|---|---|",
    ]
    for lesson in chart["four_lessons"]:
        lines.append(
            f"| {lesson['index']} | {lesson['upper']} | {lesson['lower']} | {lesson['general']} |"
        )

    lines.extend(
        [
            "",
            "## 三传",
            "| 传 | 地支 | 天将 | 六亲 | 遁干 | 空亡 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for t in chart["three_transmissions"]:
        lines.append(
            f"| {t['stage']} | {t['branch']} | {t['general']} | {t['liuqin']} | "
            f"{t['hidden_stem']} | {'是' if t['void'] else '否'} |"
        )

    lines.extend(["", "## 天地盘", "| 地盘 | " + " | ".join(p["earth"] for p in chart["plates"]) + " |",
                  "|---|" + "---|" * len(chart["plates"])])
    lines.append("| 天盘 | " + " | ".join(p["heaven"] for p in chart["plates"]) + " |")
    lines.append("| 天将 | " + " | ".join(p["general"] for p in chart["plates"]) + " |")
    lines.append("")
    lines.append("> 课盘为确定性排盘；断课需结合所问之事取用神，同一课问不同事结论不同。")
    return "\n".join(lines)
