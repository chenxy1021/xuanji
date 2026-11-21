"""小六壬起课引擎。

纯函数：不读写文件、不联网；随机只在 random 方式下取服务端随机数（无全局状态）。

起课三种方式：
- time   ：月宫从大安起正月顺数到农历月；日宫从月宫起初一顺数到日；时宫从日宫起子时顺数到时辰
- number ：三个数分别定月宫/日宫/时宫（n % 6 取宫，大安为 0）
- random ：服务端随机三宫（默认）

断事以时宫为主，月宫看起因、日宫看发展。
"""

from __future__ import annotations

import re
import secrets
from datetime import date, datetime
from typing import Any

from lunar_python import Solar

from app.core.errors import EngineError

from . import constants as C

ENGINE_VERSION = "xiaoliuren-1.0"

METHOD_NAMES = {"time": "时间起课", "number": "数字起课", "random": "随机起课"}

_METHOD_ALIASES = {
    "time": "time", "date": "time", "时间": "time",
    "number": "number", "numbers": "number", "num": "number", "数字": "number",
    "random": "random", "rand": "random", "随机": "random",
}

# 前端通用表单把 numbers 当字符串提交（如 "3,8,5"），这里统一按常见分隔符切开
_NUMBER_SPLIT = re.compile(r"[,，、+＋\s;；]+")


# --------------------------------------------------------------------------
# 输入解析
# --------------------------------------------------------------------------


def _normalize_method(raw: Any) -> str:
    if raw is None or raw == "":
        return "random"
    key = str(raw).strip().lower()
    try:
        return _METHOD_ALIASES[key]
    except KeyError as exc:
        raise EngineError(f"未知起课方式：{raw}（可选 time / number / random）") from exc


def _parse_when(options: dict[str, Any]) -> tuple[datetime, list[str]]:
    """起课时刻。缺省按当前时间。"""
    warnings: list[str] = []
    raw = options.get("date") or options.get("datetime")

    if raw is None:
        when = datetime.now().replace(second=0, microsecond=0)
    elif isinstance(raw, datetime):
        when = raw
    elif isinstance(raw, date):
        when = datetime(raw.year, raw.month, raw.day)
    else:
        try:
            when = datetime.fromisoformat(str(raw).strip())
        except ValueError as exc:
            raise EngineError(
                f"无法解析起课日期：{raw}（请用 ISO 格式，如 2025-03-05 或 2025-03-05T14:30）",
            ) from exc

    hour = options.get("hour")
    if hour is not None:
        try:
            hour_int = int(hour)
            minute_int = int(options.get("minute") or 0)
        except (TypeError, ValueError) as exc:
            raise EngineError(f"时辰格式无效：{hour}") from exc
        if not 0 <= hour_int <= 23 or not 0 <= minute_int <= 59:
            raise EngineError(f"时辰超出范围：{hour_int}:{minute_int}")
        when = when.replace(hour=hour_int, minute=minute_int)
    elif raw is not None and not isinstance(raw, datetime) and "T" not in str(raw) and " " not in str(raw):
        when = when.replace(hour=0, minute=0)
        warnings.append("未提供时辰，按子时（00:00）起课")

    return when.replace(second=0, microsecond=0), warnings


def _lunar_facts(when: datetime) -> dict[str, Any]:
    solar = Solar.fromYmdHms(when.year, when.month, when.day, when.hour, when.minute, 0)
    lunar = solar.getLunar()
    raw_month = lunar.getMonth()
    is_leap = raw_month < 0
    month = abs(raw_month)
    day = lunar.getDay()
    shichen_index = C.HOUR_TO_SHICHEN_INDEX[when.hour]
    shichen = C.SHICHEN[shichen_index]
    lunar_text = f"农历{'闰' if is_leap else ''}{_month_text(month)}月{_day_text(day)}{shichen}时"
    return {
        "month": month,
        "day": day,
        "is_leap_month": is_leap,
        "shichen": shichen,
        "shichen_index": shichen_index,
        "text": lunar_text,
    }


_CN_DIGITS = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九")


def _month_text(month: int) -> str:
    if month <= 10:
        return _CN_DIGITS[month] if month < 10 else "十"
    if month == 11:
        return "十一"
    return "十二"


def _day_text(day: int) -> str:
    if day <= 10:
        return "初" + _CN_DIGITS[day] if day < 10 else "初十"
    if day < 20:
        return "十" + _CN_DIGITS[day - 10]
    if day == 20:
        return "二十"
    if day < 30:
        return "廿" + _CN_DIGITS[day - 20]
    return "三十"


# --------------------------------------------------------------------------
# 取宫
# --------------------------------------------------------------------------


def _palace(index: int, role_index: int) -> dict[str, Any]:
    data = C.PALACES[index]
    role = C.PALACE_ROLES[role_index]
    return {
        "index": index,
        "order": index + 1,
        "name": data["name"],
        "role": role["role"],
        "role_meaning": role["meaning"],
        "role_desc": role["desc"],
        "element": data["element"],
        "direction": data["direction"],
        "deity": data["deity"],
        "luck": data["luck"],
        "omen": data["omen"],
        "advice": data["advice"],
    }


def _indices_from_time(facts: dict[str, Any]) -> list[int]:
    """月宫从大安起正月顺数到月；日宫从月宫起初一顺数到日；时宫从日宫起子时顺数到时辰。"""
    month_index = (facts["month"] - 1) % 6
    day_index = (month_index + facts["day"] - 1) % 6
    hour_index = (day_index + facts["shichen_index"]) % 6
    return [month_index, day_index, hour_index]


def _parse_numbers(raw: Any, count: int) -> list[int]:
    """解析所报之数：兼容 list/tuple 与前端表单传来的字符串（"3,8,5" / "3 8 5" / "3、8、5" / "3+8+5"）。"""
    expected = "两" if count == 2 else "三"
    example = "37,18" if count == 2 else "3,8,5"
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise EngineError(f"数字起课需要填写{expected}个数字（如 {example}）")
    if isinstance(raw, str):
        tokens = [token for token in _NUMBER_SPLIT.split(raw.strip()) if token]
    elif isinstance(raw, (list, tuple)):
        tokens = [str(item).strip() for item in raw]
        tokens = [token for token in tokens if token]
    else:
        raise EngineError(f"数字起课需要填写{expected}个数字（如 {example}），收到：{raw!r}")
    if len(tokens) != count:
        got = "、".join(tokens) if tokens else "空"
        raise EngineError(f"数字起课需要填写{expected}个数字（如 {example}），实收 {len(tokens)} 个：{got}")
    try:
        return [int(token) for token in tokens]
    except ValueError as exc:
        raise EngineError(f"数字起课的数字必须都是整数，收到：{'、'.join(tokens)}") from exc


def _number_values(options: dict[str, Any]) -> list[int]:
    values = _parse_numbers(options.get("numbers"), 3)
    bad = [value for value in values if value <= 0]
    if bad:
        raise EngineError(f"数字起课的三个数需为正整数，收到：{bad}")
    return values


def _indices_from_random() -> list[int]:
    return [secrets.randbelow(6) for _ in range(3)]


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------


def compute(options: dict[str, Any] | None = None) -> dict[str, Any]:
    opts: dict[str, Any] = dict(options or {})
    warnings: list[str] = []

    method = _normalize_method(opts.get("method"))
    when, when_warnings = _parse_when(opts)
    warnings.extend(when_warnings)
    facts = _lunar_facts(when)

    if method == "time":
        indices = _indices_from_time(facts)
        basis = (
            f"{facts['text']}：月宫从大安起正月顺数至{facts['month']}月（落{C.PALACE_ORDER[indices[0]]}），"
            f"日宫自月宫起初一顺数至{facts['day']}日（落{C.PALACE_ORDER[indices[1]]}），"
            f"时宫自日宫起子时顺数至{facts['shichen']}时（落{C.PALACE_ORDER[indices[2]]}）"
        )
    elif method == "number":
        values = _number_values(opts)
        indices = [value % 6 for value in values]
        basis = (
            f"所报三数 {values[0]}、{values[1]}、{values[2]}：第 n 数按 n % 6 取宫（大安为 0），"
            "依次定月宫、日宫、时宫"
        )
    else:
        indices = _indices_from_random()
        basis = "服务端随机取三宫，未按农历月日时顺数起课"
        warnings.append("三宫为随机所得，不体现月→日→时的顺数关系，宜自报数字或按时间起课以求连贯")

    palaces = [_palace(index, role_index) for role_index, index in enumerate(indices)]
    main = palaces[2]

    summary = (
        f"月宫{palaces[0]['name']}（{palaces[0]['luck']}）→ 日宫{palaces[1]['name']}"
        f"（{palaces[1]['luck']}）→ 时宫{main['name']}（{main['luck']}）；"
        f"断事以时宫为主：{main['omen']}{main['advice']}"
    )

    warnings.append(C.STREAM_NOTE)

    return {
        "method": method,
        "method_name": METHOD_NAMES[method],
        "cast_at": when.strftime("%Y-%m-%d %H:%M"),
        "lunar": {
            "month": facts["month"],
            "day": facts["day"],
            "is_leap_month": facts["is_leap_month"],
            "shichen": facts["shichen"],
            "text": facts["text"],
        },
        "cast": {"basis": basis, "indices": indices},
        "palaces": palaces,
        "main": main,
        "summary": summary,
        "warnings": warnings,
    }
