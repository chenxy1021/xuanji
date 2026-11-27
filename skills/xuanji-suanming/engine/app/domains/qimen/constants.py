"""奇门排盘的中文命名映射。

排盘算法由 MIT 许可的 qimen-rs（Rust + PyO3 绑定）负责，本文件只做显示层转换。
"""

from __future__ import annotations

STEMS: dict[str, str] = {
    "jia": "甲", "yi": "乙", "bing": "丙", "ding": "丁", "wu": "戊",
    "ji": "己", "geng": "庚", "xin": "辛", "ren": "壬", "gui": "癸",
}

BRANCHES: dict[str, str] = {
    "zi": "子", "chou": "丑", "yin": "寅", "mao": "卯", "chen": "辰", "si": "巳",
    "wu": "午", "wei": "未", "shen": "申", "you": "酉", "xu": "戌", "hai": "亥",
}

TRIGRAMS: dict[str, str] = {
    "kan": "坎", "kun": "坤", "zhen": "震", "xun": "巽",
    "qian": "乾", "dui": "兑", "gen": "艮", "li": "离",
}

DIRECTIONS: dict[str, str] = {
    "north": "北", "south": "南", "east": "东", "west": "西",
    "northeast": "东北", "northwest": "西北",
    "southeast": "东南", "southwest": "西南", "center": "中",
}

ELEMENTS: dict[str, str] = {
    "water": "水", "wood": "木", "fire": "火", "earth": "土", "metal": "金",
}

STARS: dict[str, str] = {
    "tian_peng": "天蓬", "tian_rui": "天芮", "tian_chong": "天冲",
    "tian_fu": "天辅", "tian_qin": "天禽", "tian_xin": "天心",
    "tian_zhu": "天柱", "tian_ren": "天任", "tian_ying": "天英",
}

DOORS: dict[str, str] = {
    "xiu": "休门", "sheng": "生门", "shang": "伤门", "du": "杜门",
    "scene": "景门", "si": "死门", "jing": "惊门", "kai": "开门",
}

DEITIES: dict[str, str] = {
    "zhi_fu": "值符", "teng_she": "腾蛇", "tai_yin": "太阴", "liu_he": "六合",
    "bai_hu": "白虎", "xuan_wu": "玄武", "jiu_di": "九地", "jiu_tian": "九天",
}

# 天干五行（用于终身局的「干落宫」生克）
STEM_ELEMENTS: dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

# 八门象意（终身局用神宫断语）
DOOR_MEANING: dict[str, str] = {
    "休门": "主休养、调停与人情往来，得休门者多能借力，宜以退为进",
    "生门": "主生机、财利与置业，生门得地则根基厚、财路活",
    "伤门": "主竞争、奔波与损伤，利于竞技执法，不利于和气生财",
    "杜门": "主闭塞、隐秘与技艺，宜专精一技，不宜张扬求名",
    "景门": "主文书、名声与消息，利考试宣传，须防虚名与口舌",
    "死门": "主终结、静止与旧事，宜收尾守成，不宜开新局",
    "惊门": "主惊恐、口舌与官非，行事宜留凭据，避免争论升级",
    "开门": "主开创、事业与通达，开门临身则格局开阔、宜向外发展",
}

STAR_MEANING: dict[str, str] = {
    "天蓬": "主智谋与冒险，胆大能成事，也易因贪快而失",
    "天任": "主稳重、勤勉与田产，宜脚踏实地积累",
    "天冲": "主行动与冲劲，利于开拓武职，忌莽撞",
    "天辅": "主文教、辅佐与学习，得贵人提携，宜以文立身",
    "天英": "主名望与火性，才华外露，须防虚华急躁",
    "天芮": "主疾病、迟滞与求学，宜调养身心、循序而进",
    "天柱": "主口舌、破坏与支撑，能言善辩，忌恃强争执",
    "天心": "主谋略、医药与管理，宜做统筹与专业之事",
    "天禽": "主中正、包容与统筹，居中调度，多方受益",
}

DEITY_MEANING: dict[str, str] = {
    "值符": "主贵人、正统与庇护，遇事多有转圜",
    "腾蛇": "主虚惊、变化与缠绕，宜防反复与心绪不宁",
    "太阴": "主隐秘与暗中相助，利筹划，不宜高调",
    "六合": "主和合、交易与婚恋，利合作与中介",
    "白虎": "主刚猛、伤病与压力，宜避锋芒、注意安全",
    "玄武": "主暧昧、失脱与欺瞒，宜防小人、看紧钱物",
    "九地": "主稳固、低调与田土，宜深耕本地、稳步经营",
    "九天": "主高远、进取与远行，利向外拓展、争取名位",
}

DUN: dict[str, str] = {"yang": "阳遁", "yin": "阴遁"}

YUAN: dict[str, str] = {"upper": "上元", "middle": "中元", "lower": "下元"}

# 九宫在页面上的排列：巽4 离9 坤2 / 震3 中5 兑7 / 艮8 坎1 乾6
GRID_ORDER: tuple[int, ...] = (4, 9, 2, 3, 5, 7, 8, 1, 6)


def stem(value: str | None) -> str:
    return STEMS.get(value or "", value or "")


def branch(value: str | None) -> str:
    return BRANCHES.get(value or "", value or "")


def star(value: str) -> str:
    return STARS.get(value, value)


def door(value: str | None) -> str:
    return DOORS.get(value or "", "—")


def deity(value: str | None) -> str:
    return DEITIES.get(value or "", "—")
