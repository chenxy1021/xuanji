"""日运 / 月运：流日、流月干支与本命盘的关系。

只回答「这一天的干支和你命局是什么关系」，不预测具体事件。
评分是维度化的启发式权重，用来看趋势，不当作吉凶判决。
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any, Literal

from lunar_python import Solar

from app.core.errors import EngineError
from app.core.types import BirthInput
from app.domains.bazi import engine as bazi_engine
from app.domains.shared.relations import (
    GAN_WUXING,
    ZHI_SHENGXIAO,
    branch_relation,
    shishen,
)

ENGINE_VERSION = "fortune-1.0"

Period = Literal["day", "month"]

_SHISHEN_EFFECT: dict[str, dict[str, int]] = {
    "比肩": {"career": 0, "wealth": -2, "love": 1, "health": 2},
    "劫财": {"career": 1, "wealth": -5, "love": 0, "health": 0},
    "食神": {"career": 2, "wealth": 3, "love": 3, "health": 4},
    "伤官": {"career": 3, "wealth": 2, "love": -2, "health": 0},
    "偏财": {"career": 1, "wealth": 5, "love": 2, "health": -1},
    "正财": {"career": 2, "wealth": 5, "love": 3, "health": 0},
    "七杀": {"career": 4, "wealth": 1, "love": -1, "health": -3},
    "正官": {"career": 5, "wealth": 2, "love": 2, "health": 0},
    "偏印": {"career": 1, "wealth": -1, "love": -1, "health": 1},
    "正印": {"career": 2, "wealth": 0, "love": 1, "health": 3},
}

_RELATION_EFFECT: dict[str, dict[str, int]] = {
    "六合": {"overall": 4, "love": 8, "career": 2},
    "三合": {"overall": 3, "love": 5, "career": 2},
    "六冲": {"overall": -4, "love": -8, "health": -3},
    "六害": {"overall": -2, "love": -4, "health": -2},
    "相刑": {"overall": -3, "love": -5, "health": -2},
}

_DO: dict[str, str] = {
    "比肩": "与同辈协作、把计划落到执行",
    "劫财": "运动、整理旧物、断舍离",
    "食神": "创作、下厨、与人轻松相处",
    "伤官": "表达观点、做需要创意的输出",
    "偏财": "谈合作、看机会、拓展人脉",
    "正财": "理财、谈薪、处理账目",
    "七杀": "处理硬骨头任务、运动消耗",
    "正官": "面谈汇报、走流程、立规矩",
    "偏印": "独自研究、复盘、学新东西",
    "正印": "读书、请教长辈、休整",
}

_AVOID: dict[str, str] = {
    "比肩": "与人争一时高下",
    "劫财": "借贷担保、冲动消费",
    "食神": "贪吃贪玩误正事",
    "伤官": "顶撞上级、口无遮拦",
    "偏财": "高风险投资、轻信许诺",
    "正财": "为小钱伤和气",
    "七杀": "硬碰硬、熬夜透支",
    "正官": "过于拘谨、因规矩内耗",
    "偏印": "钻牛角尖、胡思乱想",
    "正印": "过度依赖他人意见",
}

_LUCKY: dict[str, dict[str, str]] = {
    "木": {"color": "青、绿", "direction": "东", "element": "木"},
    "火": {"color": "红、紫", "direction": "南", "element": "火"},
    "土": {"color": "黄、棕", "direction": "西南", "element": "土"},
    "金": {"color": "白、银", "direction": "西", "element": "金"},
    "水": {"color": "黑、蓝", "direction": "北", "element": "水"},
}


def compute(birth: BirthInput, options: dict[str, Any] | None = None, period: Period = "day") -> tuple[
    dict[str, Any], list[str]
]:
    options = options or {}
    target = _parse_date(options.get("date")) if options.get("date") else date.today()

    natal, _, natal_warnings = bazi_engine.compute(birth)
    pillars = natal["pillars"]
    day_master = pillars["day"]["gan"]

    lunar = Solar.fromYmd(target.year, target.month, target.day).getLunar()
    year_gz = lunar.getYearInGanZhiByLiChun()
    month_gz = lunar.getMonthInGanZhiExact()
    day_gz = lunar.getDayInGanZhi()

    if period == "day":
        active_gz = day_gz
        label = f"{target.year}年{target.month}月{target.day}日"
        span = {"start": target.isoformat(), "end": target.isoformat()}
    else:
        active_gz = month_gz
        last_day = calendar.monthrange(target.year, target.month)[1]
        label = f"{target.year}年{target.month}月"
        span = {
            "start": date(target.year, target.month, 1).isoformat(),
            "end": date(target.year, target.month, last_day).isoformat(),
        }

    active_gan, active_zhi = active_gz[0], active_gz[1]
    star = shishen(day_master, active_gan)

    scores = {"overall": 60, "career": 60, "wealth": 60, "love": 60, "health": 60}
    for key, delta in _SHISHEN_EFFECT[star].items():
        scores[key] += delta * 2

    relations: list[dict[str, Any]] = []
    for name, zhi in (("夫妻宫", pillars["day"]["zhi"]), ("年支", pillars["year"]["zhi"])):
        for kind, detail in branch_relation(active_zhi, zhi):
            relations.append({"target": name, "kind": kind, "detail": detail})
            effect = _RELATION_EFFECT.get(kind)
            if not effect:
                continue
            scale = 1.0 if name == "夫妻宫" else 0.5
            for key, delta in effect.items():
                scores[key] += round(delta * scale)

    scores = {k: max(0, min(100, v)) for k, v in scores.items()}
    scores["overall"] = round(
        scores["career"] * 0.3 + scores["wealth"] * 0.25 + scores["love"] * 0.25 + scores["health"] * 0.2
    )

    element = GAN_WUXING[active_gan]
    chart = {
        "engine": ENGINE_VERSION,
        "period": period,
        "date": target.isoformat(),
        "span": span,
        "label": label,
        "ganzhi": {"year": year_gz, "month": month_gz, "day": day_gz, "active": active_gz},
        "day_master": day_master,
        "shishen": star,
        "relations": relations,
        "scores": scores,
        "summary": _summary(period, star, scores, relations),
        "do": [_DO[star]],
        "avoid": [_AVOID[star]],
        "lucky": _LUCKY[element],
        "natal": {
            "pillars": {k: pillars[k]["gan"] + pillars[k]["zhi"] for k in ("year", "month", "day", "hour")},
            "day_master": day_master,
            "zodiac": ZHI_SHENGXIAO[pillars["year"]["zhi"]],
        },
        "disclaimer": "流日/流月只描述当天或当月干支与命局的关系，不构成吉凶预测。",
    }
    return chart, natal_warnings


def render_text(chart: dict[str, Any]) -> str:
    title = "日运" if chart["period"] == "day" else "月运"
    z = chart["ganzhi"]
    lines = [
        f"# {title}：{chart['label']}",
        "",
        f"- 流年：{z['year']}　流月：{z['month']}　流日：{z['day']}",
        f"- 本命日主：{chart['day_master']}　与当日干支的关系：{chart['shishen']}",
        f"- 综合：{chart['scores']['overall']}/100　事业 {chart['scores']['career']}　"
        f"财运 {chart['scores']['wealth']}　感情 {chart['scores']['love']}　状态 {chart['scores']['health']}",
        f"- 一句话：{chart['summary']}",
        "",
        "## 与本命盘的关系",
    ]
    for r in chart["relations"]:
        lines.append(f"- {r['target']}：{r['kind']}（{r['detail']}）")
    lines.extend(
        [
            "",
            "## 宜忌",
            f"- 宜：{'; '.join(chart['do'])}",
            f"- 忌：{'; '.join(chart['avoid'])}",
            f"- 幸运色：{chart['lucky']['color']}　方位：{chart['lucky']['direction']}",
            "",
            f"> {chart['disclaimer']}",
        ]
    )
    return "\n".join(lines)


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise EngineError(f"日期格式应为 YYYY-MM-DD：{value}") from exc


def _summary(
    period: Period, star: str, scores: dict[str, int], relations: list[dict[str, Any]]
) -> str:
    # 只挑一个最值得说的维度
    best = max(("career", "wealth", "love", "health"), key=lambda k: scores[k])
    worst = min(("career", "wealth", "love", "health"), key=lambda k: scores[k])
    dims = {"career": "事业", "wealth": "财运", "love": "感情", "health": "状态"}

    scope = "今天" if period == "day" else "这个月"
    flow = "流日" if period == "day" else "流月"
    parts = [f"{scope}{flow}为{star}，{dims[best]}相对顺手"]
    if scores[worst] < 55:
        parts.append(f"{dims[worst]}容易卡顿，别硬推")
    hits = [r["detail"] for r in relations if r["kind"] not in ("无",)]
    if hits:
        parts.append(hits[0])
    return "；".join(parts) + "。"
