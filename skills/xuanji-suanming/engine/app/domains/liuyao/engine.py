"""六爻纳甲排盘引擎。

纯函数：不读写文件、不联网、不使用全局可变状态。
输入 options，输出可直接序列化的 chart 字典。

三种起卦方式：
- coins  ：options["lines"] = [6,7,8,9,...] 六个数，自下而上（6 老阴 / 7 少阳 / 8 少阴 / 9 老阳）
- time   ：年月日时起卦（梅花易数法），需要 options["date"] 与 options["hour"]
- number ：options["numbers"] = [n1, n2]，两数起卦

断卦要素：本卦 / 变卦 / 互卦、纳甲干支、六亲、六神、世应、动爻。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from lunar_python import Solar

from app.core.errors import EngineError

from . import constants as C

ENGINE_VERSION = "liuyao-1.0"

METHOD_NAMES = {"coins": "铜钱摇卦", "time": "时间起卦", "number": "数字起卦"}

_METHOD_ALIASES = {
    "coins": "coins", "coin": "coins", "copper": "coins", "铜钱": "coins", "摇卦": "coins",
    "time": "time", "datetime": "time", "时间": "time",
    "number": "number", "numbers": "number", "num": "number", "数字": "number",
}

# 断卦提示：本期未实现的部分统一写进 warnings，避免使用者误读
_KONG_WANG_NOTE = "空亡（旬空）本期未计算，断卦时请按日辰旬空自行校验"


# --------------------------------------------------------------------------
# 输入解析
# --------------------------------------------------------------------------


def _normalize_method(raw: Any) -> str:
    # 缺省用时间起卦：铜钱法必须要 lines，直接调接口不传 method 时不该 422
    if raw is None:
        return "time"
    key = str(raw).strip().lower()
    try:
        return _METHOD_ALIASES[key]
    except KeyError as exc:
        raise EngineError(f"未知起卦方式：{raw}（可选 coins / time / number）") from exc


def _parse_when(options: dict[str, Any]) -> tuple[datetime, list[str]]:
    """解析起卦时刻。缺省按当前时间，并给出提示。"""
    warnings: list[str] = []
    raw = options.get("date") or options.get("datetime")

    if raw is None:
        when = datetime.now().replace(second=0, microsecond=0)
        warnings.append("未提供起卦时间，已按当前时刻起卦")
    elif isinstance(raw, datetime):
        when = raw
    elif isinstance(raw, date):
        when = datetime(raw.year, raw.month, raw.day)
    else:
        text = str(raw).strip()
        try:
            when = datetime.fromisoformat(text)
        except ValueError as exc:
            raise EngineError(f"无法解析起卦时间：{raw}（请用 ISO 格式，如 2025-03-05 或 2025-03-05T14:30）") from exc

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
    elif not isinstance(raw, datetime) and raw is not None and "T" not in str(raw) and " " not in str(raw):
        when = when.replace(hour=0, minute=0)
        warnings.append("未提供时辰，月建与日辰按 00:00 计算")

    return when.replace(second=0, microsecond=0), warnings


def _lunar_facts(when: datetime) -> dict[str, Any]:
    """月建 / 日辰 / 年干支 / 农历月日，供起卦与六神使用。"""
    solar = Solar.fromYmdHms(when.year, when.month, when.day, when.hour, when.minute, 0)
    lunar = solar.getLunar()
    return {
        "year_ganzhi": lunar.getYearInGanZhi(),
        "month_ganzhi": lunar.getMonthInGanZhiExact(),
        "day_ganzhi": lunar.getDayInGanZhiExact(),
        "lunar_month": abs(lunar.getMonth()),
        "lunar_day": lunar.getDay(),
    }


# --------------------------------------------------------------------------
# 爻码推导
# --------------------------------------------------------------------------


def _trigram_code(name: str) -> str:
    return "".join(str(bit) for bit in C.TRIGRAMS[name]["binary"])  # type: ignore[union-attr]


def _code_from_trigrams(upper: str, lower: str) -> str:
    return _trigram_code(lower) + _trigram_code(upper)


def _lines_from_coins(options: dict[str, Any]) -> tuple[str, list[bool]]:
    raw = options.get("lines")
    if not isinstance(raw, (list, tuple)) or len(raw) != 6:
        raise EngineError("铜钱起卦需要 lines 六个数（自下而上，6/7/8/9）")
    try:
        values = [int(item) for item in raw]
    except (TypeError, ValueError) as exc:
        raise EngineError("lines 只能包含整数 6/7/8/9") from exc
    bad = [value for value in values if value not in C.LINE_VALUES]
    if bad:
        raise EngineError(f"爻值只能是 6/7/8/9，收到：{bad}")
    code = "".join("1" if value in C.YANG_VALUES else "0" for value in values)
    moving = [value in C.MOVING_VALUES for value in values]
    return code, moving


def _lines_from_time(options: dict[str, Any], facts: dict[str, Any], when: datetime) -> tuple[str, list[bool]]:
    """梅花易数年月日时起卦：年支数 + 农历月 + 农历日（+ 时支数）。"""
    year_branch = facts["year_ganzhi"][1]
    year_number = C.BRANCHES.index(year_branch) + 1
    month_number = int(facts["lunar_month"])
    day_number = int(facts["lunar_day"])
    hour_number = C.HOUR_TO_BRANCH_INDEX[when.hour]

    upper_sum = year_number + month_number + day_number
    lower_sum = upper_sum + hour_number
    upper = C.XIANTIAN_TO_TRIGRAM[upper_sum % 8 or 8]
    lower = C.XIANTIAN_TO_TRIGRAM[lower_sum % 8 or 8]
    dong = lower_sum % 6 or 6
    code = _code_from_trigrams(upper, lower)
    moving = [position == dong for position in range(1, 7)]
    return code, moving


def _lines_from_numbers(options: dict[str, Any]) -> tuple[str, list[bool]]:
    raw = options.get("numbers")
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise EngineError("数字起卦需要 numbers 两个整数")
    try:
        first, second = int(raw[0]), int(raw[1])
    except (TypeError, ValueError) as exc:
        raise EngineError("numbers 只能包含整数") from exc
    if first <= 0 or second <= 0:
        raise EngineError("数字起卦的两个数需为正整数")

    upper = C.XIANTIAN_TO_TRIGRAM[first % 8 or 8]
    lower = C.XIANTIAN_TO_TRIGRAM[second % 8 or 8]
    dong = (first + second) % 6 or 6
    code = _code_from_trigrams(upper, lower)
    moving = [position == dong for position in range(1, 7)]
    return code, moving


# --------------------------------------------------------------------------
# 卦体构造
# --------------------------------------------------------------------------


def _liuqin(palace_element: str, line_element: str) -> str:
    """六亲：以卦宫五行为「我」，与爻支五行论生克。"""
    if line_element == palace_element:
        return "兄弟"
    if C.SHENG[line_element] == palace_element:
        return "父母"
    if C.SHENG[palace_element] == line_element:
        return "子孙"
    if C.KE[line_element] == palace_element:
        return "官鬼"
    if C.KE[palace_element] == line_element:
        return "妻财"
    raise EngineError(f"六亲推导失败：宫{palace_element} 爻{line_element}")


def _najia_lines(code: str) -> list[tuple[str, str]]:
    """按纳甲取六爻干支：内卦（1-3 爻）用内卦纳甲，外卦（4-6 爻）用外卦纳甲。"""
    info = C.GUA_INDEX[code]
    lower = str(info["lower"])
    upper = str(info["upper"])
    inner_stem, inner_branches = C.NAJIA[lower]["inner"]
    outer_stem, outer_branches = C.NAJIA[upper]["outer"]
    result: list[tuple[str, str]] = []
    for branch in inner_branches:
        result.append((inner_stem, branch))
    for branch in outer_branches:
        result.append((outer_stem, branch))
    return result


def _gua_detail(code: str, day_stem: str, moving_positions: set[int]) -> dict[str, Any]:
    info = C.GUA_INDEX[code]
    palace_element = str(info["palace_element"])
    liushen_start = C.LIUSHEN_START_BY_STEM[day_stem]
    shi_line = int(info["shi_line"])  # type: ignore[arg-type]
    ying_line = int(info["ying_line"])  # type: ignore[arg-type]

    lines: list[dict[str, Any]] = []
    for index, (stem, branch) in enumerate(_najia_lines(code)):
        position = index + 1
        element = C.BRANCH_ELEMENT[branch]
        shi_ying: str | None = None
        if position == shi_line:
            shi_ying = "世"
        elif position == ying_line:
            shi_ying = "应"
        lines.append(
            {
                "position": position,
                "yinyang": "阳" if code[index] == "1" else "阴",
                "moving": position in moving_positions,
                "gan_zhi": f"{stem}{branch}",
                "branch": branch,
                "wuxing": element,
                "liuqin": _liuqin(palace_element, element),
                "liushen": C.LIUSHEN_ORDER[(liushen_start + index) % 6],
                "shi_ying": shi_ying,
            }
        )

    return {
        "name": info["name"],
        "full_name": info["full_name"],
        "symbol": info["symbol"],
        "binary": code,
        "upper": info["upper"],
        "lower": info["lower"],
        "palace": info["palace"],
        "element": palace_element,
        "stage": info["stage"],
        "shi_line": shi_line,
        "ying_line": ying_line,
        "lines": lines,
    }


def _hu_code(code: str) -> str:
    """互卦：下互取 2/3/4 爻，上互取 3/4/5 爻。"""
    return code[1:4] + code[2:5]


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

    if method == "coins":
        code, moving_flags = _lines_from_coins(opts)
    elif method == "time":
        code, moving_flags = _lines_from_time(opts, facts, when)
    else:
        code, moving_flags = _lines_from_numbers(opts)

    day_stem = str(facts["day_ganzhi"])[0]
    moving_positions = {index + 1 for index, flag in enumerate(moving_flags) if flag}

    ben_gua = _gua_detail(code, day_stem, moving_positions)

    bian_gua: dict[str, Any] | None = None
    if moving_positions:
        flipped = "".join(
            str(1 - int(bit)) if index + 1 in moving_positions else bit
            for index, bit in enumerate(code)
        )
        bian_gua = _gua_detail(flipped, day_stem, set())

    hu_gua = _gua_detail(_hu_code(code), day_stem, set())

    warnings.append(_KONG_WANG_NOTE)

    return {
        "method": method,
        "method_name": METHOD_NAMES[method],
        "question": str(opts.get("question") or ""),
        "cast_at": when.strftime("%Y-%m-%d %H:%M"),
        "lunar_date": f"农历{facts['lunar_month']}月{facts['lunar_day']}日",
        "year_gan_zhi": facts["year_ganzhi"],
        "month_gan_zhi": facts["month_ganzhi"],
        "day_gan_zhi": facts["day_ganzhi"],
        "moving_lines": sorted(moving_positions),
        "ben_gua": ben_gua,
        "bian_gua": bian_gua,
        "hu_gua": hu_gua,
        "warnings": warnings,
    }
