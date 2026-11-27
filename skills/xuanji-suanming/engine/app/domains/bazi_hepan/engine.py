"""八字合盘：两张本命盘之间的关系。

只做「可核对的关系判断」：天干五合/相冲、地支六合/三合/六冲/六害/相刑、
日主十神、五行互补。综合分是启发式权重，用于排序参考，不是命定结论。
"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput
from app.domains.bazi import engine as bazi_engine
from app.domains.shared.relations import (
    GAN_WUXING,
    ZHI_SHENGXIAO,
    branch_relation,
    gan_relation,
    ganzhi_wuxing_counts,
    shishen,
)

ENGINE_VERSION = "bazi-hepan-1.0"
PILLAR_KEYS = ("year", "month", "day", "hour")

_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 六合、三合、六冲等在两盘之间的权重
_WEIGHTS = {
    "日主五合": 10,
    "日主相生": 5,
    "日主相冲": -8,
    "夫妻宫六合": 12,
    "夫妻宫三合": 8,
    "夫妻宫六冲": -12,
    "夫妻宫六害": -6,
    "夫妻宫相刑": -6,
    "生肖六合": 5,
    "生肖三合": 4,
    "生肖六冲": -5,
    "生肖六害": -3,
    "生肖相刑": -3,
}


def compute(birth: BirthInput, secondary: BirthInput) -> tuple[dict[str, Any], str, list[str]]:
    chart_a, _, warn_a = bazi_engine.compute(birth)
    chart_b, _, warn_b = bazi_engine.compute(secondary)

    warnings: list[str] = ["合盘综合分是启发式权重，仅供比较参考，不构成关系判断"]
    if warn_a:
        warnings.append(f"甲方：{'；'.join(warn_a)}")
    if warn_b:
        warnings.append(f"乙方：{'；'.join(warn_b)}")

    person_a = _person(chart_a)
    person_b = _person(chart_b)

    matches: list[dict[str, Any]] = []
    score = 60

    # 日主：天干关系 + 十神
    a_day = chart_a["pillars"]["day"]["gan"]
    b_day = chart_b["pillars"]["day"]["gan"]
    for kind, detail in gan_relation(a_day, b_day):
        if kind == "五合":
            score += _WEIGHTS["日主五合"]
            matches.append({"scope": "日主", "kind": kind, "detail": detail, "effect": "positive"})
        elif kind == "相冲":
            score += _WEIGHTS["日主相冲"]
            matches.append({"scope": "日主", "kind": kind, "detail": detail, "effect": "negative"})

    if _generates(a_day, b_day):
        score += _WEIGHTS["日主相生"]
        matches.append(
            {
                "scope": "日主",
                "kind": "相生",
                "detail": f"{a_day}{GAN_WUXING[a_day]}与{b_day}{GAN_WUXING[b_day]}相生，相处中有一方更主动付出",
                "effect": "positive",
            }
        )

    matches.append(
        {
            "scope": "日主",
            "kind": "十神",
            "detail": f"甲方看乙方为{shishen(a_day, b_day)}，乙方看甲方为{shishen(b_day, a_day)}",
            "effect": "neutral",
        }
    )

    # 夫妻宫（日支）与生肖（年支）
    a_spouse = chart_a["pillars"]["day"]["zhi"]
    b_spouse = chart_b["pillars"]["day"]["zhi"]
    score += _apply_branch(matches, prefix="夫妻宫", a=a_spouse, b=b_spouse)

    a_zodiac = chart_a["pillars"]["year"]["zhi"]
    b_zodiac = chart_b["pillars"]["year"]["zhi"]
    score += _apply_branch(matches, prefix="生肖", a=a_zodiac, b=b_zodiac)

    # 五行互补
    complement = _complement(person_a["wuxing"], person_b["wuxing"])
    score += sum(item.pop("_score") for item in complement)

    score = max(0, min(100, score))

    chart_out = {
        "engine": ENGINE_VERSION,
        "a": person_a,
        "b": person_b,
        "matches": matches,
        "complement": complement,
        "score": score,
        "level": _level(score),
        "advice": _advice(matches, complement, person_a, person_b),
        "disclaimer": "合盘看的是两个人的结构差异与互补，不是好坏判决；分数只用于横向比较。",
    }
    return chart_out, "", warnings


def _person(chart: dict[str, Any]) -> dict[str, Any]:
    pillars = chart["pillars"]
    gan_list = [pillars[k]["gan"] for k in PILLAR_KEYS]
    zhi_list = [pillars[k]["zhi"] for k in PILLAR_KEYS]
    counts = ganzhi_wuxing_counts(gan_list + zhi_list)
    total = sum(counts.values()) or 1

    day_gan = pillars["day"]["gan"]

    return {
        "gender": chart["gender"],
        "solar_date": chart["solar_date"],
        "lunar_date": chart["lunar_date"],
        "shichen": chart["shichen"],
        "pillars": {k: pillars[k]["gan"] + pillars[k]["zhi"] for k in PILLAR_KEYS},
        "day_master": day_gan,
        "day_master_element": GAN_WUXING[day_gan],
        "spouse_palace": pillars["day"]["zhi"],
        "zodiac": ZHI_SHENGXIAO[pillars["year"]["zhi"]],
        "wuxing": {e: round(c / total * 100) for e, c in counts.items()},
        "missing": [e for e, c in counts.items() if c == 0],
        "strongest": [e for e, c in counts.items() if c == max(counts.values())],
        "true_solar_time": chart.get("true_solar_time"),
    }


def _generates(a: str, b: str) -> bool:
    """两个天干是否构成相生（任一方向）。"""
    ea, eb = GAN_WUXING[a], GAN_WUXING[b]
    return _SHENG[ea] == eb or _SHENG[eb] == ea


def _apply_branch(matches: list[dict[str, Any]], *, prefix: str, a: str, b: str) -> int:
    """把一对地支关系写入 matches，返回分数增量。"""
    delta = 0
    for kind, detail in branch_relation(a, b):
        if kind == "无":
            matches.append({"scope": prefix, "kind": "无", "detail": detail, "effect": "neutral"})
            continue
        weight = _WEIGHTS[f"{prefix}{kind}"]
        delta += weight
        matches.append(
            {
                "scope": prefix,
                "kind": kind,
                "detail": detail,
                "effect": "positive" if weight > 0 else "negative",
            }
        )
    return delta


def _complement(a: dict[str, int], b: dict[str, int]) -> list[dict[str, Any]]:
    """五行互补：一方缺、另一方旺，视为互补。"""
    out: list[dict[str, Any]] = []
    for element, ratio in a.items():
        if ratio == 0 and b.get(element, 0) >= 25:
            out.append(
                {
                    "scope": "五行",
                    "kind": "互补",
                    "detail": f"甲方缺{element}，乙方{element}较旺（{b[element]}%），可补甲方所短",
                    "effect": "positive",
                    "_score": 4,
                }
            )
    for element, ratio in b.items():
        if ratio == 0 and a.get(element, 0) >= 25:
            out.append(
                {
                    "scope": "五行",
                    "kind": "互补",
                    "detail": f"乙方缺{element}，甲方{element}较旺（{a[element]}%），可补乙方所短",
                    "effect": "positive",
                    "_score": 4,
                }
            )
    return out


def _level(score: int) -> str:
    if score >= 80:
        return "契合"
    if score >= 65:
        return "较合"
    if score >= 50:
        return "中等"
    if score >= 35:
        return "需磨合"
    return "差异较大"


def _advice(
    matches: list[dict[str, Any]],
    complement: list[dict[str, Any]],
    a: dict[str, Any],
    b: dict[str, Any],
) -> list[str]:
    tips: list[str] = []
    negatives = [m for m in matches if m["effect"] == "negative"]
    positives = [m for m in matches if m["effect"] == "positive"]

    if positives:
        tips.append(f"可借力之处：{positives[0]['detail']}。")
    if negatives:
        tips.append(f"需要留意：{negatives[0]['detail']}，摩擦多出现在对应的主题上。")
    if complement:
        tips.append("五行上存在互补，长期相处容易在对方身上补到自己缺的部分。")
    if set(a["strongest"]) & set(b["strongest"]) and a["strongest"] == b["strongest"]:
        tips.append(
            f"两人都以{a['strongest'][0]}为旺，优势相似、盲区也相似，决策时容易一起忽略同一类风险。"
        )
    if not tips:
        tips.append("两盘之间没有强烈的合或冲，关系更多取决于现实相处与沟通方式。")
    return tips
