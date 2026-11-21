"""紫微斗数展示层的常量。

排盘规则本身由 ziwei 库负责（见 NOTICE.md），这里只做命名与分类映射。
"""

from __future__ import annotations

BRANCH_ORDER: tuple[str, ...] = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")

# 库沿用古籍宫名，界面上用更通行的说法
PALACE_NAME_MODERN: dict[str, str] = {
    "命宫": "命宫",
    "兄弟": "兄弟",
    "妻妾": "夫妻",
    "子女": "子女",
    "财帛": "财帛",
    "疾厄": "疾厄",
    "迁移": "迁移",
    "奴仆": "交友",
    "官禄": "官禄",
    "田宅": "田宅",
    "福德": "福德",
    "父母": "父母",
}

MAJOR_STARS: frozenset[str] = frozenset(
    {"紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"}
)

LUCKY_STARS: frozenset[str] = frozenset(
    {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "天马", "红鸾", "天喜"}
)

SHA_STARS: frozenset[str] = frozenset(
    {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫", "天刑", "天姚", "天哭", "天虚", "天伤", "天使"}
)

HUA_NAMES: dict[str, str] = {"lu": "禄", "quan": "权", "ke": "科", "ji": "忌"}


def star_kind(star: str) -> str:
    if star in MAJOR_STARS:
        return "major"
    if star in LUCKY_STARS:
        return "lucky"
    if star in SHA_STARS:
        return "sha"
    return "minor"
