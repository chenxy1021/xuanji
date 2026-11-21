"""解读方向目录与提示词。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.focus import labels_for, topics_for
from app.core.prompt import build_messages
from app.domains import list_specs
from app.main import app

client = TestClient(app)


def test_every_registered_system_has_topics() -> None:
    for spec in list_specs():
        topics = topics_for(spec.id)
        assert len(topics) >= 5, spec.id
        ids = [t.id for t in topics]
        assert len(ids) == len(set(ids)), f"{spec.id} 方向 id 重复"
        assert all(t.label and t.label_en for t in topics)


def test_ziwei_topics_follow_palace_order() -> None:
    res = client.get("/api/v1/focus/ziwei")
    assert res.status_code == 200
    labels = [t["label"] for t in res.json()["topics"]]
    assert labels == [
        "命格总览",
        "财运",
        "事业",
        "感情",
        "性格",
        "健康",
        "兄弟合伙",
        "子女",
        "迁移外出",
        "人际贵人",
        "田宅",
        "福德",
        "父母长辈",
    ]


def test_unknown_system_returns_404() -> None:
    assert client.get("/api/v1/focus/not-a-system").status_code == 404


def test_labels_follow_catalog_order_and_ignore_unknown() -> None:
    # 传入顺序与目录不同，输出仍按目录顺序；伪造 id 被丢弃
    assert labels_for("ziwei", ["career", "overview", "../../etc/passwd"]) == ["命格总览", "事业"]


def test_prompt_contains_selected_focus() -> None:
    messages = build_messages(
        system="bazi",
        chart_text="日主庚金",
        chart_json="{}",
        style="concise",
        focus=labels_for("bazi", ["wealth", "career"]),
    )
    user = messages[1]["content"]
    assert "解读重点" in user
    assert "事业、财运" in user
    assert "按上面的顺序" in user


def test_prompt_without_focus_is_unchanged() -> None:
    messages = build_messages(system="bazi", chart_text="x", chart_json="{}")
    assert "解读重点" not in messages[1]["content"]
    assert "整体解读" in messages[1]["content"]
