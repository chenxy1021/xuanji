"""干支关系表：五行、十神、合冲刑害。

合盘、日运等跨体系模块共用，避免各处重复维护一张互不相同的表。
"""

from __future__ import annotations

from collections.abc import Iterable

GAN_WUXING: dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

ZHI_WUXING: dict[str, str] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

GAN_YINYANG: dict[str, str] = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
}

ZHI_SHENGXIAO: dict[str, str] = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
    "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}

# 天干五合
GAN_HE: dict[frozenset[str], str] = {
    frozenset({"甲", "己"}): "土",
    frozenset({"乙", "庚"}): "金",
    frozenset({"丙", "辛"}): "水",
    frozenset({"丁", "壬"}): "木",
    frozenset({"戊", "癸"}): "火",
}

# 天干相冲（戊己居中不冲）
GAN_CHONG: set[frozenset[str]] = {
    frozenset({"甲", "庚"}),
    frozenset({"乙", "辛"}),
    frozenset({"丙", "壬"}),
    frozenset({"丁", "癸"}),
}

# 地支六合
ZHI_LIUHE: dict[frozenset[str], str] = {
    frozenset({"子", "丑"}): "土",
    frozenset({"寅", "亥"}): "木",
    frozenset({"卯", "戌"}): "火",
    frozenset({"辰", "酉"}): "金",
    frozenset({"巳", "申"}): "水",
    frozenset({"午", "未"}): "土",
}

# 地支三合局
ZHI_SANHE: list[tuple[frozenset[str], str]] = [
    (frozenset({"申", "子", "辰"}), "水"),
    (frozenset({"亥", "卯", "未"}), "木"),
    (frozenset({"寅", "午", "戌"}), "火"),
    (frozenset({"巳", "酉", "丑"}), "金"),
]

# 地支六冲
ZHI_CHONG: set[frozenset[str]] = {
    frozenset({"子", "午"}),
    frozenset({"丑", "未"}),
    frozenset({"寅", "申"}),
    frozenset({"卯", "酉"}),
    frozenset({"辰", "戌"}),
    frozenset({"巳", "亥"}),
}

# 地支六害
ZHI_HAI: set[frozenset[str]] = {
    frozenset({"子", "未"}),
    frozenset({"丑", "午"}),
    frozenset({"寅", "巳"}),
    frozenset({"卯", "辰"}),
    frozenset({"申", "亥"}),
    frozenset({"酉", "戌"}),
}

# 地支相刑：组内任意两字（含同字自刑）成刑
ZHI_XING: list[tuple[frozenset[str], str]] = [
    (frozenset({"寅", "巳", "申"}), "无恩之刑"),
    (frozenset({"丑", "戌", "未"}), "恃势之刑"),
    (frozenset({"子", "卯"}), "无礼之刑"),
    (frozenset({"辰"}), "自刑"),
    (frozenset({"午"}), "自刑"),
    (frozenset({"酉"}), "自刑"),
    (frozenset({"亥"}), "自刑"),
]

_SHENG: dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE: dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def gan_wuxing(gan: str) -> str:
    return GAN_WUXING[gan]


def zhi_wuxing(zhi: str) -> str:
    return ZHI_WUXING[zhi]


def shishen(day_gan: str, other_gan: str) -> str:
    """以 day_gan 为「我」，求 other_gan 的十神。"""
    me = GAN_WUXING[day_gan]
    other = GAN_WUXING[other_gan]
    same_polarity = GAN_YINYANG[day_gan] == GAN_YINYANG[other_gan]

    if other == me:
        return "比肩" if same_polarity else "劫财"
    if _SHENG[me] == other:
        return "食神" if same_polarity else "伤官"
    if _KE[me] == other:
        return "偏财" if same_polarity else "正财"
    if _KE[other] == me:
        return "七杀" if same_polarity else "正官"
    if _SHENG[other] == me:
        return "偏印" if same_polarity else "正印"
    raise ValueError(f"无法判定十神：{day_gan} → {other_gan}")


def ganzhi_wuxing_counts(ganzhi: Iterable[str]) -> dict[str, int]:
    """统计四柱八字的五行个数（天干、地支各计一，不计藏干）。"""
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for item in ganzhi:
        if item in GAN_WUXING:
            counts[GAN_WUXING[item]] += 1
        elif item in ZHI_WUXING:
            counts[ZHI_WUXING[item]] += 1
    return counts


def branch_relation(a: str, b: str) -> list[tuple[str, str]]:
    """返回两地支之间的关系，元素为 (类型, 说明)。

    类型固定为：六合 / 三合 / 六冲 / 六害 / 相刑 / 无。
    """
    pair = frozenset({a, b})
    out: list[tuple[str, str]] = []

    if pair in ZHI_LIUHE:
        out.append(("六合", f"{a}{b}六合化{ZHI_LIUHE[pair]}"))

    for group, element in ZHI_SANHE:
        if a in group and b in group and a != b:
            out.append(("三合", f"{a}{b}同属{'、'.join(sorted(group))}三合{element}局"))

    if pair in ZHI_CHONG:
        out.append(("六冲", f"{a}{b}相冲"))

    if pair in ZHI_HAI:
        out.append(("六害", f"{a}{b}相害"))

    for group, label in ZHI_XING:
        if len(group) == 1:
            if a == b and a in group:
                out.append(("相刑", f"{a}{b}{label}"))
        elif a != b and a in group and b in group:
            out.append(("相刑", f"{a}{b}{label}"))

    return out or [("无", f"{a}{b}无特殊刑冲合害")]


def gan_relation(a: str, b: str) -> list[tuple[str, str]]:
    pair = frozenset({a, b})
    out: list[tuple[str, str]] = []
    if pair in GAN_HE:
        out.append(("五合", f"{a}{b}相合化{GAN_HE[pair]}"))
    if pair in GAN_CHONG:
        out.append(("相冲", f"{a}{b}相冲"))
    return out or [("无", f"{a}{b}无合冲")]
