"""解读文风与回答语言：通俗解释术语、去掉 AI 套话、跟随提问语言。"""

from __future__ import annotations

from app.api.routes.interpret import _answer_lang
from app.core.focus import labels_for
from app.core.prompt import build_messages


def test_focus_labels_follow_english() -> None:
    assert labels_for("bazi", ["wealth", "career"], "en") == ["Career", "Wealth"]
    assert labels_for("bazi", ["wealth", "career"]) == ["事业", "财运"]


def test_divination_prompt_asks_for_plain_language() -> None:
    messages = build_messages(
        system="liuyao",
        chart_text="本卦：困",
        chart_json="{}",
        question="这份工作要不要接",
        focus=labels_for("liuyao", ["overview", "advice"]),
    )
    system = messages[0]["content"]
    user = messages[1]["content"]
    # 明确要求先给答案、翻译术语、不要固定三段式
    assert "先把答案说出来" in system
    assert "大白话" in system
    assert "核心论断 / 盘面依据 / 现实建议" in system
    assert "不是…而是…" in system
    # 六爻有自己的讲解提示，且带上所选方向
    assert "六爻" in user
    assert "世爻" in user
    assert "所问之事" in user


def test_answer_language_follows_question() -> None:
    assert _answer_lang("zh", "Will I get this job?") == "en"
    assert _answer_lang("en", "这份工作能成吗？") == "zh"
    assert _answer_lang("en", "2026?") == "en"
    assert _answer_lang("en", None) == "en"
    assert _answer_lang("zh", None) == "zh"


def test_english_prompt_uses_english_labels_and_messages() -> None:
    messages = build_messages(
        system="liuyao",
        chart_text="本卦：困",
        chart_json="{}",
        question="Should I take this job?",
        focus=labels_for("liuyao", ["overview", "advice"], "en"),
        lang="en",
    )
    system = messages[0]["content"]
    user = messages[1]["content"]
    assert "English" in system
    assert "The question" in user
    assert "What to do" in user
    # 英文回答也要求保留中文专名并解释
    assert "保留中文" in system
