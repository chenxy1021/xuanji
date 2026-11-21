"""紫微合盘：两张命盘的宫位互看。

判断依据只有三类，全部可回溯到盘面：
1. 双方命宫地支的六合/三合/六冲/六害/相刑
2. 一方命宫主星是否落在对方夫妻宫，以及双方夫妻宫主星是否相同
3. 一方生年四化是否飞入对方命宫/夫妻宫/福德宫

综合分是启发式权重，不是命定结论。
"""

from __future__ import annotations

from typing import Any

from app.core.types import BirthInput
from app.domains.shared.relations import branch_relation
from app.domains.ziwei import engine as ziwei_engine

ENGINE_VERSION = "ziwei-hepan-1.0"

FOCUS_PALACES = ("命宫", "夫妻", "福德")

# 命宫地支关系权重
_BRANCH_WEIGHTS = {"六合": 10, "三合": 7, "六冲": -10, "六害": -4, "相刑": -5, "无": 0}

# 四化飞入对方宫位的权重
_HUA_WEIGHTS = {
    ("命宫", "禄"): 6,
    ("命宫", "权"): 5,
    ("命宫", "科"): 4,
    ("命宫", "忌"): -6,
    ("夫妻", "禄"): 7,
    ("夫妻", "权"): 5,
    ("夫妻", "科"): 4,
    ("夫妻", "忌"): -8,
    ("福德", "禄"): 5,
    ("福德", "权"): 4,
    ("福德", "科"): 3,
    ("福德", "忌"): -5,
}


def compute(birth: BirthInput, secondary: BirthInput) -> tuple[dict[str, Any], str, list[str]]:
    chart_a, _, warn_a = ziwei_engine.compute(birth)
    chart_b, _, warn_b = ziwei_engine.compute(secondary)

    warnings: list[str] = ["紫微合盘综合分为启发式权重，仅供参考，不构成关系判断"]
    if warn_a:
        warnings.append(f"甲方：{'；'.join(warn_a)}")
    if warn_b:
        warnings.append(f"乙方：{'；'.join(warn_b)}")

    a = _person(chart_a)
    b = _person(chart_b)

    matches: list[dict[str, Any]] = []
    score = 60

    # 1. 命宫地支
    for kind, detail in branch_relation(a["ming_branch"], b["ming_branch"]):
        weight = _BRANCH_WEIGHTS.get(kind, 0)
        score += weight
        matches.append(
            {
                "scope": "命宫",
                "kind": kind,
                "detail": detail,
                "effect": "positive" if weight > 0 else "negative" if weight < 0 else "neutral",
            }
        )

    # 2. 命宫主星 ↔ 对方夫妻宫
    a_ming = set(a["ming_stars"])
    b_ming = set(b["ming_stars"])
    a_spouse = set(a["spouse_stars"])
    b_spouse = set(b["spouse_stars"])

    for star in sorted(a_ming & b_spouse):
        score += 8
        matches.append(
            {
                "scope": "星曜",
                "kind": "吸引",
                "detail": f"甲方命宫{star}，正落在乙方夫妻宫，乙容易被甲的气质吸引",
                "effect": "positive",
            }
        )
    for star in sorted(b_ming & a_spouse):
        score += 8
        matches.append(
            {
                "scope": "星曜",
                "kind": "吸引",
                "detail": f"乙方命宫{star}，正落在甲方夫妻宫，甲容易被乙的气质吸引",
                "effect": "positive",
            }
        )
    for star in sorted(a_spouse & b_spouse):
        score += 5
        matches.append(
            {
                "scope": "星曜",
                "kind": "同构",
                "detail": f"双方夫妻宫同见{star}，对亲密关系的期待有相似之处",
                "effect": "positive",
            }
        )

    # 3. 四化飞入
    for side, own, other in (("甲", a, b), ("乙", b, a)):
        for hua, star in own["sihua"].items():
            palace = _palace_of_star(other, star)
            if palace is None:
                continue
            weight = _HUA_WEIGHTS.get((palace["name"], hua))
            if weight is None:
                continue
            score += weight
            matches.append(
                {
                    "scope": "四化",
                    "kind": f"{star}化{hua}",
                    "detail": f"{side}方{star}化{hua}，落入对方{palace['name']}（{palace['branch']}宫）",
                    "effect": "positive" if weight > 0 else "negative",
                }
            )

    score = max(0, min(100, score))

    chart_out = {
        "engine": ENGINE_VERSION,
        "a": a,
        "b": b,
        "matches": matches,
        "score": score,
        "level": _level(score),
        "advice": _advice(matches),
        "disclaimer": "紫微合盘看的是宫位与星曜的呼应关系，样本越多越容易「都对」，请当作观察角度而非结论。",
    }
    return chart_out, "", warnings


def _person(chart: dict[str, Any]) -> dict[str, Any]:
    palaces = chart["palaces"]
    ming = next(p for p in palaces if p["is_ming"])
    spouse = next(p for p in palaces if p["name"] == "夫妻")
    fude = next(p for p in palaces if p["name"] == "福德")

    return {
        "gender": chart["gender"],
        "solar_date": chart["solar_date"],
        "lunar_date": chart["lunar_date"],
        "shichen": chart["shichen"],
        "bureau": chart["bureau"],
        "ming_branch": chart["ming_gong"],
        "shen_branch": chart["shen_gong"],
        "ming_stars": _major_stars(ming),
        "spouse_branch": spouse["branch"],
        "spouse_stars": _major_stars(spouse),
        "fude_branch": fude["branch"],
        "fude_stars": _major_stars(fude),
        "sihua": chart.get("sihua", {}),
        "palaces": [
            {
                "branch": p["branch"],
                "name": p["name"],
                "stem": p["stem"],
                "is_ming": p["is_ming"],
                "stars": [
                    {"name": s["name"], "kind": s["kind"], "sihua": s.get("sihua")}
                    for s in p["stars"]
                ],
            }
            for p in palaces
        ],
    }


def _major_stars(palace: dict[str, Any]) -> list[str]:
    return [s["name"] for s in palace["stars"] if s["kind"] == "major"]


def _palace_of_star(person: dict[str, Any], star: str) -> dict[str, Any] | None:
    for palace in person["palaces"]:
        if any(s["name"] == star for s in palace["stars"]):
            return palace
    return None


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


def _advice(matches: list[dict[str, Any]]) -> list[str]:
    tips: list[str] = []
    positives = [m for m in matches if m["effect"] == "positive"]
    negatives = [m for m in matches if m["effect"] == "negative"]

    if positives:
        tips.append(f"最明显的呼应：{positives[0]['detail']}。")
    if negatives:
        tips.append(f"最需要留意：{negatives[0]['detail']}，这类张力往往在相处两三年后显现。")
    if not positives and not negatives:
        tips.append("两盘之间没有强烈的呼应或冲突，关系走向更多取决于现实选择。")
    tips.append("命宫主星为空宫时，吸引力判断会偏弱，可结合三方四正一起看。")
    return tips
