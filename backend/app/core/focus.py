"""AI 解读方向目录。

前端只传方向 id，后端在这里映射为受控标签再拼进提示词，
避免把任意文本直接塞进 system prompt。方向顺序固定，保证同一组选择
每次生成的提示词一致。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FocusTopic:
    id: str
    label: str
    label_en: str


_OVERVIEW = FocusTopic("overview", "命格总览", "Overall chart")

TOPICS: dict[str, list[FocusTopic]] = {
    "bazi": [
        _OVERVIEW,
        FocusTopic("personality", "性格", "Personality"),
        FocusTopic("career", "事业", "Career"),
        FocusTopic("wealth", "财运", "Wealth"),
        FocusTopic("love", "感情", "Relationships"),
        FocusTopic("health", "健康", "Health"),
        FocusTopic("family", "家庭", "Family"),
        FocusTopic("social", "人际", "Social life"),
        FocusTopic("study", "学业", "Learning"),
        FocusTopic("annual", "近年运势", "Recent years"),
    ],
    # 紫微的方向与十二宫一一对应，顺序沿用命宫起、逆布十二宫的习惯
    "ziwei": [
        _OVERVIEW,
        FocusTopic("wealth", "财运", "Wealth"),
        FocusTopic("career", "事业", "Career"),
        FocusTopic("love", "感情", "Relationships"),
        FocusTopic("personality", "性格", "Personality"),
        FocusTopic("health", "健康", "Health"),
        FocusTopic("siblings", "兄弟合伙", "Siblings & partners"),
        FocusTopic("children", "子女", "Children"),
        FocusTopic("travel", "迁移外出", "Travel & relocation"),
        FocusTopic("social", "人际贵人", "Friends & benefactors"),
        FocusTopic("property", "田宅", "Home & property"),
        FocusTopic("wellbeing", "福德", "Wellbeing"),
        FocusTopic("parents", "父母长辈", "Parents & elders"),
    ],
    "astrology": [
        _OVERVIEW,
        FocusTopic("personality", "性格", "Personality"),
        FocusTopic("career", "事业", "Career"),
        FocusTopic("wealth", "财运", "Wealth"),
        FocusTopic("love", "感情", "Relationships"),
        FocusTopic("health", "健康", "Health"),
        FocusTopic("family", "家庭", "Family"),
        FocusTopic("social", "人际", "Social life"),
        FocusTopic("growth", "成长课题", "Growth"),
    ],
    "qimen": [
        _OVERVIEW,
        FocusTopic("career", "事业", "Career"),
        FocusTopic("wealth", "财运", "Wealth"),
        FocusTopic("love", "感情", "Relationships"),
        FocusTopic("health", "健康", "Health"),
        FocusTopic("social", "人际", "Social life"),
        FocusTopic("travel", "出行迁移", "Travel"),
        FocusTopic("property", "田宅", "Home & property"),
    ],
    "bazi_hepan": [
        FocusTopic("overview", "关系总览", "Relationship overview"),
        FocusTopic("attraction", "吸引力", "Attraction"),
        FocusTopic("communication", "沟通方式", "Communication"),
        FocusTopic("conflict", "冲突点", "Conflict points"),
        FocusTopic("longterm", "长期发展", "Long-term outlook"),
        FocusTopic("family", "家庭与长辈", "Family & elders"),
    ],
    "ziwei_hepan": [
        FocusTopic("overview", "关系总览", "Relationship overview"),
        FocusTopic("attraction", "吸引力", "Attraction"),
        FocusTopic("communication", "沟通方式", "Communication"),
        FocusTopic("conflict", "冲突点", "Conflict points"),
        FocusTopic("longterm", "长期发展", "Long-term outlook"),
        FocusTopic("family", "家庭与长辈", "Family & elders"),
    ],
    "liuyao": [
        FocusTopic("overview", "所问之事", "The question"),
        FocusTopic("timing", "时机", "Timing"),
        FocusTopic("advice", "应对建议", "What to do"),
        FocusTopic("risk", "风险提醒", "Risks"),
        FocusTopic("people", "人际", "People"),
        FocusTopic("wealth", "财物", "Money"),
    ],
    "meihua": [
        FocusTopic("overview", "所问之事", "The question"),
        FocusTopic("timing", "时机", "Timing"),
        FocusTopic("advice", "应对建议", "What to do"),
        FocusTopic("risk", "风险提醒", "Risks"),
        FocusTopic("people", "人际", "People"),
        FocusTopic("wealth", "财物", "Money"),
    ],
    "tarot": [
        FocusTopic("overview", "牌阵总览", "Spread overview"),
        FocusTopic("situation", "现状", "Situation"),
        FocusTopic("obstacle", "阻碍", "Obstacles"),
        FocusTopic("advice", "建议", "Advice"),
        FocusTopic("outcome", "趋势", "Outlook"),
    ],
    "kongming": [
        FocusTopic("overview", "签文总览", "Lot overview"),
        FocusTopic("question", "所问之事", "The question"),
        FocusTopic("timing", "时机", "Timing"),
        FocusTopic("advice", "应对建议", "What to do"),
        FocusTopic("risk", "风险提醒", "Risks"),
    ],
    "mbti": [
        FocusTopic("overview", "性格总览", "Type overview"),
        FocusTopic("strengths", "优势", "Strengths"),
        FocusTopic("blindspots", "盲点", "Blind spots"),
        FocusTopic("career", "职业倾向", "Work style"),
        FocusTopic("relationships", "关系模式", "Relationships"),
        FocusTopic("growth", "成长建议", "Growth"),
    ],
}

DEFAULT_TOPICS = [_OVERVIEW]


def topics_for(system: str) -> list[FocusTopic]:
    return TOPICS.get(system, DEFAULT_TOPICS)


def as_dicts(system: str) -> list[dict[str, str]]:
    return [asdict(topic) for topic in topics_for(system)]


def labels_for(system: str, ids: list[str] | None) -> list[str]:
    """按目录顺序返回选中方向的标签；未知 id 直接忽略。"""
    if not ids:
        return []
    wanted = set(ids)
    return [topic.label for topic in topics_for(system) if topic.id in wanted]
