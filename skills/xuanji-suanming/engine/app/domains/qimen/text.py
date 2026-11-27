"""奇门终身局 → 给 LLM 的规范文本。"""

from __future__ import annotations

from typing import Any


def _palace_name(p: dict[str, Any]) -> str:
    return "中宫" if p["trigram"] == "中" else f"{p['trigram']}（{p['direction']}）"


def render(chart: dict[str, Any]) -> str:
    life = chart["lifelong"]
    lines = [
        "# 奇门终身局（拆补转盘）",
        "",
        f"- 出生时刻：{chart['datetime']}（{chart['lunar_date']}）",
        f"- 四柱：{' '.join(chart['four_pillars'][k] for k in ('year', 'month', 'day', 'hour'))}"
        f"　生肖：{life['zodiac']}",
        f"- 节气：{chart['solar_term']}（下一节气 {chart['next_solar_term']}）",
        f"- 局：{chart['ju_text']}（{chart['yuan']}）",
        f"- 旬首：{chart['xun']['head']}（遁{chart['xun']['hidden_stem']}）"
        f"　空亡：{'、'.join(chart['xun']['void_branches']) or '无'}",
        f"- 值符：{chart['leaders']['star']}（{chart['leaders']['star_palace']}宫）"
        f"　值使：{chart['leaders']['door']}（{chart['leaders']['door_palace']}宫）",
        f"- 马星：{chart['horse']['branch']}（{chart['horse']['palace']}宫）",
        "",
        "## 三宫用神",
        "",
    ]

    for anchor in life["anchors"]:
        lines.append(f"### {anchor['label']}：{anchor['ganzhi']}（{anchor['role']}）")
        lines.append("")
        if anchor["palace"] is None:
            lines.append("- 该天干未见于地盘，暂不作断。")
            lines.append("")
            continue
        p = anchor["palace"]
        lines.append(
            f"- 落宫：{p['number']}宫 {_palace_name(p)}（{p['element']}）；"
            f"依据：{anchor['basis']}"
        )
        lines.append(f"- 门星神：{p['door']} · {'、'.join(p['stars']) or '无星'} · {p['deity']}")
        lines.append(f"- 干宫生克：{anchor['relation']['name']}——{anchor['relation']['note']}")
        if p["void_branches"]:
            lines.append(f"- 空亡：{'、'.join(p['void_branches'])}")
        if p["is_horse"]:
            lines.append("- 马星临宫：主变动、远行、迁移")
        for reading in anchor["readings"]:
            lines.append(f"- {reading}")
        lines.append(f"- 小结：{anchor['summary']}")
        lines.append("")

    lines.extend(
        [
            "## 九宫",
            "| 宫 | 方位 | 地盘 | 天盘 | 九星 | 八门 | 八神 | 备注 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for p in chart["grid"]:
        notes: list[str] = []
        if p["is_horse"]:
            notes.append("马星")
        if p["void_branches"]:
            notes.append(f"空亡{'、'.join(p['void_branches'])}")
        lines.append(
            f"| {p['number']} | {_palace_name(p)} | {p['earth_stem']} | "
            f"{'、'.join(p['heaven_stems']) or '—'} | {'、'.join(p['stars']) or '—'} | "
            f"{p['door']} | {p['deity']} | {'；'.join(notes) or '—'} |"
        )
    lines.append("")
    lines.append("## 解读提示")
    lines.append("")
    lines.append("- 先读三宫用神，再以九宫为背景；年命看一生底色，日干看本人，时干看事业与晚运。")
    lines.append("- 门、星、神与干宫生克要合看，不要只凭一个符号断吉凶。")
    lines.append("- 只依据上表盘面推断，不得改动宫位、门星神与局数。")
    lines.append(f"- {life['note']}")
    lines.append("")
    return "\n".join(lines)
