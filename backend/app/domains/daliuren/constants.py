"""大六壬显示层命名。"""

from __future__ import annotations

GENERALS: dict[str, str] = {
    "貴": "贵人", "蛇": "螣蛇", "雀": "朱雀", "合": "六合", "勾": "勾陈", "龍": "青龙",
    "空": "天空", "虎": "白虎", "常": "太常", "玄": "玄武", "陰": "太阴", "后": "天后",
}

LIUQIN: dict[str, str] = {
    "父母": "父母", "子孫": "子孙", "財妻": "妻财", "兄弟": "兄弟", "官鬼": "官鬼",
    # 上游库在三传里返回单字
    "父": "父母", "子": "子孙", "財": "妻财", "财": "妻财", "兄": "兄弟", "官": "官鬼",
}

# 月将（太阳过宫）对照
MONTH_GENERAL: dict[str, str] = {
    "亥": "登明", "戌": "河魁", "酉": "从魁", "申": "传送", "未": "小吉", "午": "胜光",
    "巳": "太乙", "辰": "天罡", "卯": "太冲", "寅": "功曹", "丑": "大吉", "子": "神后",
}

# 旬空
VOID_BY_XUN: dict[str, tuple[str, str]] = {
    "甲子": ("戌", "亥"), "甲戌": ("申", "酉"), "甲申": ("午", "未"),
    "甲午": ("辰", "巳"), "甲辰": ("寅", "卯"), "甲寅": ("子", "丑"),
}

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

PATTERN_FIXES: dict[str, str] = {
    "遙尅": "遥克", "賊尅": "贼克", "比用": "比用", "涉害": "涉害", "昴星": "昴星",
    "別責": "别责", "八專": "八专", "伏吟": "伏吟", "返吟": "返吟",
    "重審": "重审", "元首": "元首", "知一": "知一",
}


def general(value: str | None) -> str:
    return GENERALS.get(value or "", value or "—")


def liuqin(value: str | None) -> str:
    return LIUQIN.get(value or "", value or "—")


def pattern(value: str) -> str:
    return PATTERN_FIXES.get(value, value)


def xun_of(day_ganzhi: str) -> str:
    """日干支所在旬的旬首。"""
    return _xun_head(_ganzhi_index(day_ganzhi))


def _ganzhi_index(gz: str) -> int:
    gan, zhi = gz[0], gz[1]
    for i in range(60):
        if GAN[i % 10] == gan and ZHI[i % 12] == zhi:
            return i
    raise ValueError(gz)


def _xun_head(index: int) -> str:
    start = index - index % 10
    return GAN[start % 10] + ZHI[start % 12]


def void_branches(day_ganzhi: str) -> list[str]:
    head = _xun_head(_ganzhi_index(day_ganzhi))
    return list(VOID_BY_XUN[head])
