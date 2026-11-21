"""六爻纳甲常量表。

只放数据，不放逻辑：八卦（符号/五行/先天数）、纳甲（内外卦干支）、
六十四卦（卦名/八宫/世应）、六亲、六神（六兽）等。

约定：
- 六爻统一「自下而上」编号，初爻为 1，上爻为 6。
- 二进制表示同样自下而上，阳爻 1、阴爻 0，写成 6 位字符串。
"""

from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------
# 干支与五行
# --------------------------------------------------------------------------

STEMS: Final[tuple[str, ...]] = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
BRANCHES: Final[tuple[str, ...]] = (
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
)

STEM_ELEMENT: Final[dict[str, str]] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

BRANCH_ELEMENT: Final[dict[str, str]] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 五行生克：SHENG 为「我生」，KE 为「我克」
SHENG: Final[dict[str, str]] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE: Final[dict[str, str]] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# --------------------------------------------------------------------------
# 八卦
# --------------------------------------------------------------------------

# binary 为自下而上三爻（1 阳 / 0 阴）；xiantian 为先天八卦数（梅花易数用）
TRIGRAMS: Final[dict[str, dict[str, object]]] = {
    "乾": {"symbol": "☰", "binary": (1, 1, 1), "element": "金", "xiantian": 1, "nature": "天"},
    "兑": {"symbol": "☱", "binary": (1, 1, 0), "element": "金", "xiantian": 2, "nature": "泽"},
    "离": {"symbol": "☲", "binary": (1, 0, 1), "element": "火", "xiantian": 3, "nature": "火"},
    "震": {"symbol": "☳", "binary": (1, 0, 0), "element": "木", "xiantian": 4, "nature": "雷"},
    "巽": {"symbol": "☴", "binary": (0, 1, 1), "element": "木", "xiantian": 5, "nature": "风"},
    "坎": {"symbol": "☵", "binary": (0, 1, 0), "element": "水", "xiantian": 6, "nature": "水"},
    "艮": {"symbol": "☶", "binary": (0, 0, 1), "element": "土", "xiantian": 7, "nature": "山"},
    "坤": {"symbol": "☷", "binary": (0, 0, 0), "element": "土", "xiantian": 8, "nature": "地"},
}

BINARY_TO_TRIGRAM: Final[dict[tuple[int, int, int], str]] = {
    trigram["binary"]: name  # type: ignore[misc]
    for name, trigram in TRIGRAMS.items()
}

# 先天八卦数 -> 卦名（余数为 0 时作 8，即坤）
XIANTIAN_TO_TRIGRAM: Final[dict[int, str]] = {
    int(trigram["xiantian"]): name  # type: ignore[arg-type]
    for name, trigram in TRIGRAMS.items()
}

# --------------------------------------------------------------------------
# 纳甲：每个卦作内卦（1-3 爻）与外卦（4-6 爻）时的干支
# --------------------------------------------------------------------------

NAJIA: Final[dict[str, dict[str, tuple[str, tuple[str, str, str]]]]] = {
    "乾": {"inner": ("甲", ("子", "寅", "辰")), "outer": ("壬", ("午", "申", "戌"))},
    "坤": {"inner": ("乙", ("未", "巳", "卯")), "outer": ("癸", ("丑", "亥", "酉"))},
    "震": {"inner": ("庚", ("子", "寅", "辰")), "outer": ("庚", ("午", "申", "戌"))},
    "巽": {"inner": ("辛", ("丑", "亥", "酉")), "outer": ("辛", ("未", "巳", "卯"))},
    "坎": {"inner": ("戊", ("寅", "辰", "午")), "outer": ("戊", ("申", "戌", "子"))},
    "离": {"inner": ("己", ("卯", "丑", "亥")), "outer": ("己", ("酉", "未", "巳"))},
    "艮": {"inner": ("丙", ("辰", "午", "申")), "outer": ("丙", ("戌", "子", "寅"))},
    "兑": {"inner": ("丁", ("巳", "卯", "丑")), "outer": ("丁", ("亥", "酉", "未"))},
}

# --------------------------------------------------------------------------
# 六十四卦：卦名（二进制 -> 卦名）
# --------------------------------------------------------------------------

GUA_NAMES: Final[dict[str, str]] = {
    "111111": "乾", "000000": "坤",
    "100010": "屯", "010001": "蒙", "111010": "需", "010111": "讼",
    "010000": "师", "000010": "比", "111011": "小畜", "110111": "履",
    "111000": "泰", "000111": "否", "101111": "同人", "111101": "大有",
    "001000": "谦", "000100": "豫", "100110": "随", "011001": "蛊",
    "110000": "临", "000011": "观", "100101": "噬嗑", "101001": "贲",
    "000001": "剥", "100000": "复", "100111": "无妄", "111001": "大畜",
    "100001": "颐", "011110": "大过", "010010": "坎", "101101": "离",
    "001110": "咸", "011100": "恒", "001111": "遁", "111100": "大壮",
    "000101": "晋", "101000": "明夷", "101011": "家人", "110101": "睽",
    "001010": "蹇", "010100": "解", "110001": "损", "100011": "益",
    "111110": "夬", "011111": "姤", "000110": "萃", "011000": "升",
    "010110": "困", "011010": "井", "101110": "革", "011101": "鼎",
    "100100": "震", "001001": "艮", "001011": "渐", "110100": "归妹",
    "101100": "丰", "001101": "旅", "011011": "巽", "110110": "兑",
    "010011": "涣", "110010": "节", "110011": "中孚", "001100": "小过",
    "101010": "既济", "010101": "未济",
}

# 文王卦序（用于取 Unicode 卦符 U+4DC0 起）
KING_WEN_NUMBER: Final[dict[str, int]] = {
    name: index
    for index, name in enumerate(
        (
            "乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履",
            "泰", "否", "同人", "大有", "谦", "豫", "随", "蛊", "临", "观",
            "噬嗑", "贲", "剥", "复", "无妄", "大畜", "颐", "大过", "坎", "离",
            "咸", "恒", "遁", "大壮", "晋", "明夷", "家人", "睽", "蹇", "解",
            "损", "益", "夬", "姤", "萃", "升", "困", "井", "革", "鼎",
            "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "涣", "节",
            "中孚", "小过", "既济", "未济",
        ),
        start=1,
    )
}

# --------------------------------------------------------------------------
# 京房八宫：宫序 -> 卦，世爻位置
# --------------------------------------------------------------------------

PALACE_ORDER: Final[tuple[str, ...]] = ("乾", "兑", "离", "震", "巽", "坎", "艮", "坤")

PALACE_ELEMENT: Final[dict[str, str]] = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八宫内八卦的生成：以本宫卦为底，依次变动的爻位（自下而上，1 起）
_PALACE_FLIPS: Final[tuple[tuple[int, ...], ...]] = (
    (),                # 本宫卦（八纯卦）
    (1,),              # 一世卦
    (1, 2),            # 二世卦
    (1, 2, 3),         # 三世卦
    (1, 2, 3, 4),      # 四世卦
    (1, 2, 3, 4, 5),   # 五世卦
    (1, 2, 3, 5),      # 游魂卦
    (5,),              # 归魂卦
)

_PALACE_STAGE_NAMES: Final[tuple[str, ...]] = (
    "本宫", "一世", "二世", "三世", "四世", "五世", "游魂", "归魂",
)

_PALACE_SHI: Final[tuple[int, ...]] = (6, 1, 2, 3, 4, 5, 4, 3)


def _ying(shi: int) -> int:
    return shi + 3 if shi <= 3 else shi - 3


def _build_gua_index() -> dict[str, dict[str, object]]:
    """按京房八宫推导每一卦的卦宫、世应，并与卦名表对齐。"""
    index: dict[str, dict[str, object]] = {}
    for palace in PALACE_ORDER:
        base = [int(bit) for bit in "".join(str(b) for b in TRIGRAMS[palace]["binary"]) * 2]  # type: ignore[union-attr]
        for stage, flips in enumerate(_PALACE_FLIPS):
            lines = list(base)
            for position in flips:
                lines[position - 1] ^= 1
            code = "".join(str(bit) for bit in lines)
            name = GUA_NAMES[code]
            upper = BINARY_TO_TRIGRAM[tuple(lines[3:6])]  # type: ignore[arg-type]
            lower = BINARY_TO_TRIGRAM[tuple(lines[0:3])]  # type: ignore[arg-type]
            shi = _PALACE_SHI[stage]
            index[code] = {
                "name": name,
                "full_name": _full_name(upper, lower, name),
                "symbol": chr(0x4DC0 + KING_WEN_NUMBER[name] - 1),
                "binary": code,
                "upper": upper,
                "lower": lower,
                "palace": palace,
                "palace_element": PALACE_ELEMENT[palace],
                "stage": _PALACE_STAGE_NAMES[stage],
                "shi_line": shi,
                "ying_line": _ying(shi),
            }
    return index


def _full_name(upper: str, lower: str, name: str) -> str:
    """拼出通行全名：八纯卦为「乾为天」，其余为「天风姤」式。"""
    if upper == lower:
        return f"{name}为{TRIGRAMS[upper]['nature']}"
    return f"{TRIGRAMS[upper]['nature']}{TRIGRAMS[lower]['nature']}{name}"


GUA_INDEX: Final[dict[str, dict[str, object]]] = _build_gua_index()
assert len(GUA_INDEX) == 64, "八宫推导未覆盖 64 卦"

# --------------------------------------------------------------------------
# 六亲 / 六神
# --------------------------------------------------------------------------

LIUQIN_NAMES: Final[tuple[str, ...]] = ("父母", "兄弟", "子孙", "妻财", "官鬼")

# 六神（六兽）自下而上循环，起点由日干决定
LIUSHEN_ORDER: Final[tuple[str, ...]] = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")

LIUSHEN_START_BY_STEM: Final[dict[str, int]] = {
    "甲": 0, "乙": 0,   # 甲乙起青龙
    "丙": 1, "丁": 1,   # 丙丁起朱雀
    "戊": 2,            # 戊起勾陈
    "己": 3,            # 己起螣蛇
    "庚": 4, "辛": 4,   # 庚辛起白虎
    "壬": 5, "癸": 5,   # 壬癸起玄武
}

# 爻值与老少阴阳：6 老阴、7 少阳、8 少阴、9 老阳（6/9 为动爻）
LINE_VALUES: Final[dict[int, str]] = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}
MOVING_VALUES: Final[frozenset[int]] = frozenset({6, 9})
YANG_VALUES: Final[frozenset[int]] = frozenset({7, 9})

# 时支序号（子 1 ... 亥 12），按整点划分
HOUR_TO_BRANCH_INDEX: Final[dict[int, int]] = {
    **{23: 1, 0: 1},
    **{h: (h + 1) // 2 + 1 for h in range(1, 23)},
}
