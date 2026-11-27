"""奇门终身局（拆补转盘）适配层。

算法来自 MIT 许可的 qimen-rs（https://github.com/SpenserCai/qimen-rs），
本文件负责：解析出生时刻 → 排盘 → 转成中文 canonical JSON，并补出
年命宫、日干宫、时干宫三个终身局用神。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from qimen_rs import calculate

from app.core.errors import EngineError
from app.core.types import BirthInput

from . import constants as C
from .constants import (
    BRANCHES,
    DEITIES,
    DIRECTIONS,
    DOORS,
    DUN,
    ELEMENTS,
    GRID_ORDER,
    STARS,
    STEMS,
    TRIGRAMS,
    YUAN,
)

ENGINE_VERSION = "qimen-0.3.0-lifelong"
METHOD_LABEL = "奇门终身局·拆补转盘"

_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def compute(
    birth: BirthInput | None, options: dict[str, Any] | None = None
) -> tuple[dict[str, Any], list[str]]:
    from app.domains.shared.moment import resolve_moment

    moment, warnings = resolve_moment(birth, options)
    if birth is not None and birth.place is None:
        warnings.append("未提供出生地，按东八区标准时间起局；补上出生地可做真太阳时校正")

    try:
        raw = calculate(
            {
                "year": moment.year,
                "month": moment.month,
                "day": moment.day,
                "hour": moment.hour,
                "minute": moment.minute,
                "utc_offset_minutes": 480,
                "day_boundary": "zi_start",
            }
        )
    except (ValueError, TypeError) as exc:
        raise EngineError(f"奇门排盘失败：{exc}") from exc

    chart = _serialize(raw, moment)
    chart["kind"] = "lifelong"
    chart["lifelong"] = _lifelong(chart)
    return chart, warnings


def _lifelong(chart: dict[str, Any]) -> dict[str, Any]:
    """以出生四柱的天干定三个用神宫：年命、日干、时干。"""
    from app.domains.shared.relations import ZHI_SHENGXIAO

    pillars = chart["four_pillars"]
    year_gz = pillars["year"]
    anchors = [
        ("year_ming", "年命宫", year_gz, "一生的底色、格局与长期走势"),
        ("day", "日干宫", pillars["day"], "本人的性情、当下状态与自身作为"),
        ("hour", "时干宫", pillars["hour"], "事业、子女、晚运与最终所成"),
    ]
    out = []
    for key, label, ganzhi, role in anchors:
        out.append(_anchor(chart, key, label, ganzhi, role))

    return {
        "method": METHOD_LABEL,
        "year_ming": out[0],
        "day": out[1],
        "hour": out[2],
        "anchors": out,
        "zodiac": ZHI_SHENGXIAO.get(year_gz[1], ""),
        "note": "终身局以年命落宫看一生底色，日干看本人，时干看事业与晚运；三宫互参，不单看一宫。",
    }


def _anchor(
    chart: dict[str, Any], key: str, label: str, ganzhi: str, role: str
) -> dict[str, Any]:
    stem = ganzhi[0]
    palace, basis = _stem_palace(chart, stem)
    if palace is None:
        return {
            "key": key,
            "label": label,
            "ganzhi": ganzhi,
            "stem": stem,
            "role": role,
            "basis": "该天干未见于地盘",
            "palace": None,
            "readings": [],
            "summary": "",
        }

    star = palace["stars"][0] if palace["stars"] else ""
    readings = [
        C.DOOR_MEANING.get(palace["door"], ""),
        C.STAR_MEANING.get(star, ""),
        C.DEITY_MEANING.get(palace["deity"], ""),
    ]
    element = C.STEM_ELEMENTS.get(stem, "")
    relation = _element_relation(palace["element"], element)
    summary = (
        f"{stem}{element}落{palace['trigram']}宫（{palace['direction']}，{palace['element']}）："
        f"{palace['door']}临{palace['deity']}，{star}守宫。{relation['note']}"
    )

    return {
        "key": key,
        "label": label,
        "ganzhi": ganzhi,
        "stem": stem,
        "stem_element": element,
        "role": role,
        "basis": basis,
        "palace": palace,
        "star": star,
        "relation": relation,
        "readings": [r for r in readings if r],
        "summary": summary,
    }


def _stem_palace(chart: dict[str, Any], stem: str) -> tuple[dict[str, Any] | None, str]:
    by_number = {p["number"]: p for p in chart["palaces"]}
    if stem == "甲":
        palace = by_number.get(chart["leaders"]["star_palace"])
        return palace, "甲遁于六仪，以值符所临之宫为用"
    hits = [
        p
        for p in chart["palaces"]
        if p["earth_stem"] == stem or p.get("hosted_earth_stem") == stem
    ]
    if not hits:
        return None, ""
    # 中五宫寄坤二宫：优先取非中宫的落点
    hits.sort(key=lambda p: p["number"] == 5)
    palace = hits[0]
    basis = "地盘落宫" if palace["earth_stem"] == stem else "地盘寄宫"
    return palace, basis


def _element_relation(palace_element: str, stem_element: str) -> dict[str, str]:
    if not palace_element or not stem_element:
        return {"name": "", "note": ""}
    if palace_element == stem_element:
        return {"name": "比和", "note": "宫与干同气，行事有底气，宜守正。"}
    if _SHENG.get(palace_element) == stem_element:
        return {"name": "宫生干", "note": "宫生干，环境助我，得地得势。"}
    if _SHENG.get(stem_element) == palace_element:
        return {"name": "干生宫", "note": "干生宫，我多付出，宜量力而行。"}
    if _KE.get(palace_element) == stem_element:
        return {"name": "宫克干", "note": "宫克干，受环境制约，宜顺势化解。"}
    return {"name": "干克宫", "note": "干克宫，能主动驾驭局面，忌用力过猛。"}


def _serialize(raw: Any, moment: datetime) -> dict[str, Any]:
    calendar = raw["calendar"]
    pillars = {
        key: f"{STEMS[p['stem']]}{BRANCHES[p['branch']]}"
        for key, p in calendar["four_pillars"].items()
    }

    palaces = [_palace(p) for p in raw["palaces"]]
    by_number = {p["number"]: p for p in palaces}
    grid = [by_number[n] for n in GRID_ORDER]

    leaders = raw["leaders"]
    xun = raw["xun"]

    return {
        "engine": ENGINE_VERSION,
        "method": METHOD_LABEL,
        "datetime": moment.strftime("%Y-%m-%d %H:%M"),
        "four_pillars": pillars,
        "solar_term": calendar["solar_term"]["name"],
        "next_solar_term": calendar["next_solar_term"]["name"],
        "lunar_date": calendar["lunar_date"]["name"],
        "dun": DUN.get(raw["dun"], raw["dun"]),
        "yuan": YUAN.get(raw["yuan"], raw["yuan"]),
        "ju": raw["ju"],
        "ju_text": f"{DUN.get(raw['dun'], '')}{_chinese_number(raw['ju'])}局",
        "xun": {
            "head": f"{STEMS[xun['head']['stem']]}{BRANCHES[xun['head']['branch']]}",
            "hidden_stem": STEMS.get(xun["hidden_stem"], xun["hidden_stem"]),
            "void_branches": [BRANCHES[b] for b in xun["void_branches"]],
        },
        "leaders": {
            "star": STARS.get(leaders["star"], leaders["star"]),
            "door": DOORS.get(leaders["door"], leaders["door"]),
            "original_palace": leaders["original_palace"],
            "star_palace": leaders["star_palace"],
            "door_palace": leaders["door_palace"],
        },
        "horse": {
            "branch": BRANCHES[raw["horse"]["branch"]],
            "palace": raw["horse"]["palace"],
        },
        "palaces": palaces,
        "grid": grid,
        "conventions": raw.get("conventions", {}),
    }


def _palace(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": p["number"],
        "trigram": TRIGRAMS.get(p["trigram"] or "", "中"),
        "direction": DIRECTIONS.get(p["direction"], p["direction"]),
        "element": ELEMENTS.get(p["element"], p["element"]),
        "earth_stem": STEMS.get(p["earth_stem"], p["earth_stem"]),
        "hosted_earth_stem": STEMS.get(p["hosted_earth_stem"], p["hosted_earth_stem"])
        if p.get("hosted_earth_stem")
        else None,
        "heaven_stems": [STEMS.get(h["stem"], h["stem"]) for h in p["heaven_stems"]],
        "stars": [STARS.get(s, s) for s in p["stars"]],
        "door": DOORS.get(p["door"], p["door"]) if p["door"] else "—",
        "deity": DEITIES.get(p["deity"], p["deity"]) if p["deity"] else "—",
        "void_branches": [BRANCHES[b] for b in p["void_branches"]],
        "is_horse": p["is_horse"],
    }


def _chinese_number(n: int) -> str:
    return {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}.get(
        n, str(n)
    )
