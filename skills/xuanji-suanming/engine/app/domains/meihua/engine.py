"""梅花易数起卦引擎。

纯函数：不读写文件、不联网、无全局可变状态。

起卦两法：
- time   ：上卦=(年支序+农历月+农历日)%8，下卦=(再+时支序)%8，动爻=总和%6（0 记作 8 / 6）
- number ：上卦=第一数%8，下卦=第二数%8，动爻=(两数和)%6

必算：本卦、互卦（2/3/4 爻为下卦，3/4/5 爻为上卦）、变卦（动爻翻转）、体卦用卦与五行生克断语。
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from lunar_python import Solar

from app.core.errors import EngineError

from . import constants as C

ENGINE_VERSION = "meihua-1.0"

METHOD_NAMES = {"time": "时间起卦", "number": "数字起卦"}

_METHOD_ALIASES = {
    "time": "time", "datetime": "time", "date": "time", "时间": "time",
    "number": "number", "numbers": "number", "num": "number", "数字": "number",
}

# 前端通用表单把 numbers 当字符串提交（如 "37,18"），这里统一按常见分隔符切开
_NUMBER_SPLIT = re.compile(r"[,，、+＋\s;；]+")

# 时支序（子 = 1，用于「年支序 + 月 + 日 + 时支序」）
_SHICHEN_INDEX_BY_HOUR: dict[int, int] = {
    **{23: 1, 0: 1},
    **{hour: (hour + 1) // 2 + 1 for hour in range(1, 23)},
}

_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")


# --------------------------------------------------------------------------
# 输入解析
# --------------------------------------------------------------------------


def _normalize_method(raw: Any) -> str:
    if raw is None or raw == "":
        return "time"
    key = str(raw).strip().lower()
    try:
        return _METHOD_ALIASES[key]
    except KeyError as exc:
        raise EngineError(f"未知起卦方式：{raw}（可选 time / number）") from exc


def _parse_when(options: dict[str, Any]) -> tuple[datetime, list[str]]:
    """起卦时刻。缺省按当前时间。"""
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
                f"无法解析起卦时间：{raw}（请用 ISO 格式，如 2025-03-05 或 2025-03-05T14:30）",
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
        warnings.append("未提供时辰，时支序按子时计")

    return when.replace(second=0, microsecond=0), warnings


def _lunar_facts(when: datetime) -> dict[str, Any]:
    solar = Solar.fromYmdHms(when.year, when.month, when.day, when.hour, when.minute, 0)
    lunar = solar.getLunar()
    year_ganzhi = lunar.getYearInGanZhi()
    year_branch = year_ganzhi[1]
    return {
        "year_ganzhi": year_ganzhi,
        "year_branch": year_branch,
        "year_number": _BRANCHES.index(year_branch) + 1,
        "lunar_month": abs(lunar.getMonth()),
        "lunar_day": lunar.getDay(),
        "is_leap_month": lunar.getMonth() < 0,
        "shichen_index": _SHICHEN_INDEX_BY_HOUR[when.hour],
        "shichen": _BRANCHES[_SHICHEN_INDEX_BY_HOUR[when.hour] - 1],
    }


# --------------------------------------------------------------------------
# 卦体
# --------------------------------------------------------------------------


def _trigram_code(name: str) -> str:
    return "".join(str(bit) for bit in C.TRIGRAMS[name]["binary"])  # type: ignore[union-attr]


def _gua(code: str) -> dict[str, Any]:
    lower = C.BINARY_TO_TRIGRAM[tuple(int(bit) for bit in code[0:3])]  # type: ignore[index]
    upper = C.BINARY_TO_TRIGRAM[tuple(int(bit) for bit in code[3:6])]  # type: ignore[index]
    info = C.HEXAGRAMS[code]
    return {
        "name": info["name"],
        "symbol": C.SYMBOL_BY_NAME[info["name"]],
        "yixiang": info["yixiang"],
        "code": code,
        "upper": upper,
        "lower": lower,
        "upper_element": C.TRIGRAM_ELEMENT[upper],
        "lower_element": C.TRIGRAM_ELEMENT[lower],
        "upper_symbol": C.TRIGRAMS[upper]["symbol"],
        "lower_symbol": C.TRIGRAMS[lower]["symbol"],
    }


def _hu_code(code: str) -> str:
    """互卦：下互取 2/3/4 爻，上互取 3/4/5 爻。"""
    return code[1:4] + code[2:5]


def _bian_code(code: str, moving_line: int) -> str:
    index = moving_line - 1
    return code[:index] + ("0" if code[index] == "1" else "1") + code[index + 1 :]


def _relation(ti_element: str, yong_element: str) -> dict[str, str]:
    """体用五行生克：用生体吉、体生用泄、体克用小吉、用克体凶、比和吉。"""
    if ti_element == yong_element:
        key = "bihe"
    elif C.SHENG[yong_element] == ti_element:
        key = "yong_sheng_ti"
    elif C.SHENG[ti_element] == yong_element:
        key = "ti_sheng_yong"
    elif C.KE[ti_element] == yong_element:
        key = "ti_ke_yong"
    elif C.KE[yong_element] == ti_element:
        key = "yong_ke_ti"
    else:  # pragma: no cover - 五行穷尽，此处不可达
        raise EngineError(f"体用关系推导失败：体{ti_element} 用{yong_element}")
    info = C.RELATION_TEXT[key]
    return {"code": key, "name": info["name"], "result": info["result"], "explain": info["explain"]}


# --------------------------------------------------------------------------
# 起卦
# --------------------------------------------------------------------------


def _derive_by_time(facts: dict[str, Any]) -> dict[str, Any]:
    base = facts["year_number"] + facts["lunar_month"] + facts["lunar_day"]
    total = base + facts["shichen_index"]
    upper_number = total - facts["shichen_index"]  # 上卦不用时支
    upper = upper_number % 8 or 8
    lower = total % 8 or 8
    moving = total % 6 or 6
    return {
        "upper_number": upper_number,
        "upper_mod": upper,
        "lower_number": total,
        "lower_mod": lower,
        "moving_number": total,
        "moving": moving,
        "detail": (
            f"{facts['year_ganzhi']}年（{facts['year_branch']}支序{facts['year_number']}）"
            f"农历{facts['lunar_month']}月{facts['lunar_day']}日{facts['shichen']}时"
            f"（时支序{facts['shichen_index']}）：上卦数 {upper_number}%8={upper}，"
            f"下卦数 {total}%8={lower}，动爻数 {total}%6={moving}"
        ),
    }


def _parse_numbers(raw: Any, count: int) -> list[int]:
    """解析所报之数：兼容 list/tuple 与前端表单传来的字符串（"37,18" / "37 18" / "37、18" / "37+18"）。"""
    expected = "两" if count == 2 else "三"
    example = "37,18" if count == 2 else "3,8,5"
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise EngineError(f"数字起卦需要填写{expected}个数字（如 {example}）")
    if isinstance(raw, str):
        tokens = [token for token in _NUMBER_SPLIT.split(raw.strip()) if token]
    elif isinstance(raw, (list, tuple)):
        tokens = [str(item).strip() for item in raw]
        tokens = [token for token in tokens if token]
    else:
        raise EngineError(f"数字起卦需要填写{expected}个数字（如 {example}），收到：{raw!r}")
    if len(tokens) != count:
        got = "、".join(tokens) if tokens else "空"
        raise EngineError(f"数字起卦需要填写{expected}个数字（如 {example}），实收 {len(tokens)} 个：{got}")
    try:
        return [int(token) for token in tokens]
    except ValueError as exc:
        raise EngineError(f"数字起卦的数字必须都是整数，收到：{'、'.join(tokens)}") from exc


def _derive_by_number(options: dict[str, Any]) -> dict[str, Any]:
    first, second = _parse_numbers(options.get("numbers"), 2)
    if first <= 0 or second <= 0:
        raise EngineError("数字起卦的两个数需为正整数")

    upper = first % 8 or 8
    lower = second % 8 or 8
    total = first + second
    moving = total % 6 or 6
    return {
        "upper_number": first,
        "upper_mod": upper,
        "lower_number": second,
        "lower_mod": lower,
        "moving_number": total,
        "moving": moving,
        "detail": (
            f"所报两数 {first}、{second}：上卦数 {first}%8={upper}，下卦数 {second}%8={lower}，"
            f"动爻数({first}+{second})%6={moving}"
        ),
    }


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

    derivation = _derive_by_time(facts) if method == "time" else _derive_by_number(opts)

    upper = C.XIANTIAN_TO_TRIGRAM[derivation["upper_mod"]]
    lower = C.XIANTIAN_TO_TRIGRAM[derivation["lower_mod"]]
    moving_line = int(derivation["moving"])

    code = _trigram_code(lower) + _trigram_code(upper)
    ben_gua = _gua(code)
    hu_gua = _gua(_hu_code(code))
    bian_gua = _gua(_bian_code(code, moving_line))

    # 动爻所在之卦为用，另一卦为体
    if moving_line <= 3:
        ti, yong, ti_position = upper, lower, "上卦"
    else:
        ti, yong, ti_position = lower, upper, "下卦"
    ti_element = C.TRIGRAM_ELEMENT[ti]
    yong_element = C.TRIGRAM_ELEMENT[yong]
    relation = _relation(ti_element, yong_element)

    judgement = (
        f"本卦{ben_gua['name']}：{ben_gua['yixiang']}。"
        f"动在{C.MOVING_LINE_NAMES[moving_line - 1]}，{ti_position}{ti}（{ti_element}）为体、"
        f"{yong}（{yong_element}）为用，{relation['name']}，{relation['result']}——{relation['explain']}。"
        f"互卦{hu_gua['name']}看中段：{hu_gua['yixiang']}。"
        f"变卦{bian_gua['name']}看落点：{bian_gua['yixiang']}。"
    )

    return {
        "method": method,
        "method_name": METHOD_NAMES[method],
        "cast_at": when.strftime("%Y-%m-%d %H:%M"),
        "lunar": {
            "month": facts["lunar_month"],
            "day": facts["lunar_day"],
            "is_leap_month": facts["is_leap_month"],
            "shichen": facts["shichen"],
            "year_ganzhi": facts["year_ganzhi"],
        },
        "cast": {
            "detail": derivation["detail"],
            "upper_number": derivation["upper_number"],
            "upper_mod": derivation["upper_mod"],
            "lower_number": derivation["lower_number"],
            "lower_mod": derivation["lower_mod"],
            "moving_number": derivation["moving_number"],
            "moving_mod": derivation["moving"],
        },
        "ben": ben_gua,
        "hu": hu_gua,
        "bian": bian_gua,
        "moving_line": moving_line,
        "moving_line_name": C.MOVING_LINE_NAMES[moving_line - 1],
        "ti_yong": {
            "ti": {"trigram": ti, "element": ti_element, "position": ti_position},
            "yong": {
                "trigram": yong,
                "element": yong_element,
                "position": "下卦" if ti_position == "上卦" else "上卦",
            },
        },
        "relation": relation,
        "judgement": judgement,
        "warnings": warnings,
    }
