"""中英切换的接口契约：英文元数据（/systems）与 MBTI 英文题干。

约定：没有翻译就留 None，不要留空串；默认 zh 的行为保持不变。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.domains import DOMAINS
from app.domains.mbti.constants import DIMENSIONS, QUESTION_TEXT_EN, QUESTIONS, SCALE
from app.main import app

client = TestClient(app)

# 任务指定的英文名，逐一核对，避免各 domain 自己起名跑偏
EXPECTED_NAMES_EN = {
    "bazi": "Four Pillars (Bazi)",
    "ziwei": "Zi Wei Dou Shu",
    "astrology": "Western Astrology",
    "qimen": "Qi Men Lifelong Chart",
    "bazi_hepan": "Bazi Synastry",
    "ziwei_hepan": "Ziwei Synastry",
    "liuyao": "Liu Yao (Six Lines)",
    "tarot": "Tarot",
    "meihua": "Meihua Yishu",
    "kongming": "Kongming Oracle",
    "mbti": "MBTI Test",
}


def _ready_ids() -> list[str]:
    return [spec_id for spec_id, module in DOMAINS.items() if module.SPEC.status == "ready"]


def _is_english(text: str) -> bool:
    """粗判英文：主体是 ASCII 字母，且不含汉字/中文标点。"""
    letters = sum(ch.isascii() and ch.isalpha() for ch in text)
    return letters >= max(8, len(text) // 3) and all(ord(ch) < 0x2E80 for ch in text)


def test_every_ready_system_has_english_name_and_tagline() -> None:
    ids = _ready_ids()
    assert len(ids) == 11
    for spec_id in ids:
        spec = DOMAINS[spec_id].SPEC
        assert spec.name_en, f"{spec_id} 缺 name_en"
        assert spec.tagline_en, f"{spec_id} 缺 tagline_en"
        assert spec.name_en.strip() == spec.name_en
        assert spec.tagline_en.strip() == spec.tagline_en


def test_english_names_match_the_agreed_wording() -> None:
    for spec_id, expect in EXPECTED_NAMES_EN.items():
        assert DOMAINS[spec_id].SPEC.name_en == expect, f"{spec_id} 英文名应为 {expect}"


def test_every_option_field_has_english_label() -> None:
    for spec_id in _ready_ids():
        for field in DOMAINS[spec_id].SPEC.fields:
            assert field.label_en, f"{spec_id}.{field.key} 缺 label_en"
            # 选项文案也算字段文案，英文界面下不该只剩中文
            for option in field.options or []:
                assert option.get("label_en"), f"{spec_id}.{field.key} 选项 {option['value']} 缺 label_en"


def test_untranslated_fields_are_none_not_empty_string() -> None:
    """没翻译就留 None；空串会被前端当成「有英文」而显示成空白。"""
    for spec_id in _ready_ids():
        spec = DOMAINS[spec_id].SPEC
        for value in (spec.name_en, spec.tagline_en):
            if value is not None:
                assert value.strip(), f"{spec_id} 有空的英文元数据"
        for field in spec.fields:
            for value in (field.label_en, field.placeholder_en, field.hint_en):
                if value is not None:
                    assert value.strip(), f"{spec_id}.{field.key} 有空的英文字段文案"


def test_systems_endpoint_carries_english_fields() -> None:
    body = client.get("/api/v1/systems").json()
    assert len(body) == 11
    by_id = {item["id"]: item for item in body}
    for spec_id in _ready_ids():
        item = by_id[spec_id]
        assert item["name_en"], f"/systems 里 {spec_id} 缺 name_en"
        assert item["tagline_en"], f"/systems 里 {spec_id} 缺 tagline_en"
        assert item["name"] and item["tagline"], "中文字段不应受影响"
    kongming = by_id["kongming"]
    questions = {field["key"]: field for field in kongming["fields"]}
    assert questions["characters"]["label_en"] == "Three characters"
    assert questions["characters"]["placeholder_en"] == "e.g. 佑咱统"


def test_mbti_quiz_defaults_to_chinese() -> None:
    body = client.get("/api/v1/quizzes/mbti").json()
    assert body["text_lang"] == "zh"
    assert body["name"] == "MBTI 测试"
    assert body["scale"]["labels"] == SCALE["labels"]
    assert [q["text"] for q in body["questions"]] == [q["text"] for q in QUESTIONS]
    assert [dim["left_name"] for dim in body["dimensions"]] == [dim["left_name"] for dim in DIMENSIONS]


def test_mbti_quiz_english_questions_and_scale() -> None:
    body = client.get("/api/v1/quizzes/mbti?lang=en").json()
    assert body["text_lang"] == "en"
    assert body["name"] == "MBTI Test"
    assert len(body["questions"]) == 32
    assert body["scale"]["labels"] == [
        "Strongly disagree",
        "Disagree",
        "Not sure",
        "Agree",
        "Strongly agree",
    ]
    first = body["questions"][0]
    assert first["text"] == QUESTION_TEXT_EN[first["id"]]
    assert _is_english(first["text"])
    assert [dim["left_name"] for dim in body["dimensions"]] == [
        "Extraverted",
        "Sensing",
        "Thinking",
        "Judging",
    ]
    for question in body["questions"]:
        assert _is_english(question["text"]), f"{question['id']} 不是英文：{question['text']}"
        # 维度和极向仍是稳定代码，前端判分逻辑不受语言影响
        assert question["dim"] in {"EI", "SN", "TF", "JP"}
        assert question["pole"] in {"E", "I", "S", "N", "T", "F", "J", "P"}


def test_mbti_quiz_rejects_unknown_language() -> None:
    resp = client.get("/api/v1/quizzes/mbti?lang=fr")
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "unsupported_lang"


def test_mbti_lang_accepts_region_forms() -> None:
    for value in ("en", "EN", "en-US", "en_US"):
        body = client.get(f"/api/v1/quizzes/mbti?lang={value}").json()
        assert body["text_lang"] == "en", value
