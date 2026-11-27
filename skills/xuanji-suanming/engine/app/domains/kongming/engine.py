"""孔明神卦（诸葛神数）起卦引擎。

纯函数：不读写文件（静态数据只读）、不联网、无全局可变状态。

起卦法：
1. 心中默念所问之事，写下三个汉字；
2. 每字取康熙笔画，超过十画只取个位（十画、二十画记作 0）；
3. 三字依次作百、十、个位组成三位数；
4. 超过 384 就反复减 384，落到 1–384；得 0 时取第 384 签。
"""

from __future__ import annotations

import re
from typing import Any

from app.core.errors import EngineError

from . import constants as C
from . import data

ENGINE_VERSION = "kongming-1.0"
METHOD_LABEL = "诸葛神数·孔明神卦"

_HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
LOT_TOTAL = 384


def _characters(raw: Any) -> list[str]:
    chars = _HAN.findall(str(raw or ""))
    if len(chars) < 3:
        raise EngineError("孔明神卦需要三个汉字，请心中默念所问之事后写下三个字")
    if len(chars) > 3:
        raise EngineError(f"孔明神卦只需三个字，当前识别到 {len(chars)} 个汉字")
    return chars


def _stroke(char: str) -> tuple[str, int]:
    """返回 (实际取画的字, 康熙笔画)。简体按常用繁体折算。"""
    table = data.strokes()
    alt = data.traditional_map().get(char)
    counted = alt if alt and alt in table else char
    if counted not in table:
        raise EngineError(f"缺少「{char}」的笔画数据，请换一个字")
    return counted, table[counted]


def _lot_number(raw: int) -> tuple[int, list[int]]:
    steps: list[int] = []
    number = raw
    while number > LOT_TOTAL:
        number -= LOT_TOTAL
        steps.append(number)
    if number == 0:
        number = LOT_TOTAL
    return number, steps


def compute(options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    chars = _characters(options.get("characters") or options.get("char"))

    counted: list[str] = []
    strokes: list[int] = []
    digits: list[int] = []
    for char in chars:
        target, count = _stroke(char)
        counted.append(target)
        strokes.append(count)
        digits.append(count % 10)

    raw_number = digits[0] * 100 + digits[1] * 10 + digits[2]
    number, steps = _lot_number(raw_number)

    row = data.lot(number)
    if row is None:  # 数据完整性兜底，正常不会发生
        raise EngineError(f"第 {number} 签缺失，请稍后重试")

    level = row["fortune"].removesuffix("签")
    meta = C.LEVELS.get(level, C.LEVELS[C.DEFAULT_LEVEL])

    parts = []
    for char, target, count, digit in zip(chars, counted, strokes, digits, strict=True):
        shown = char if target == char else f"{char}→{target}"
        parts.append(f"{shown} {count} 画取 {digit}")
    detail = "；".join(parts) + f"，得 {raw_number:03d}"
    if steps:
        trail = "−".join([str(raw_number), *["384"] * len(steps)])
        detail += f"；{trail}={number}"
    elif raw_number == 0:
        detail += "；0 记作第 384 签"
    else:
        detail += f"，即第 {number} 签"

    return {
        "engine": ENGINE_VERSION,
        "method": METHOD_LABEL,
        "method_name": "三字取签",
        "question": str(options.get("question") or "").strip(),
        "characters": chars,
        "counted_characters": counted,
        "strokes": strokes,
        "digits": digits,
        "calculation": {
            "raw": raw_number,
            "subtractions": steps,
            "number": number,
            "detail": detail,
        },
        "lot": {
            "number": row["number"],
            "fortune": row["fortune"],
            "level": level,
            "palace": f"{row['palace']}宫",
            "hexagram": row["hexagram"],
            "changed": row["changed"],
            "line": row["line"],
            "poem": row["poem"],
        },
        "reading": {
            "tone": meta["tone"],
            "keywords": list(meta["keywords"]),
            "advice": meta["advice"],
        },
        "disclaimer": C.DISCLAIMER,
        "warnings": [],
    }
