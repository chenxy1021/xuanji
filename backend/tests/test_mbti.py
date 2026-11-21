from fastapi.testclient import TestClient

from app.domains.mbti.constants import QUESTIONS
from app.main import app

client = TestClient(app)


def _answers(pick_left: bool) -> list[int]:
    """左极题答 5、右极题答 1（或相反），得到纯左/纯右。"""
    left = {"E", "S", "T", "J"}
    out: list[int] = []
    for q in QUESTIONS:
        is_left = q["pole"] in left
        agree = 5 if (is_left == pick_left) else 1
        out.append(agree)
    return out


def test_quiz_exposes_all_questions() -> None:
    body = client.get("/api/v1/quizzes/mbti").json()
    assert body["id"] == "mbti"
    assert len(body["questions"]) == 32
    assert {q["dim"] for q in body["questions"]} == {"EI", "SN", "TF", "JP"}


def test_pure_left_gives_estj() -> None:
    resp = client.post("/api/v1/charts/mbti", json={"options": {"answers": _answers(True)}})
    assert resp.status_code == 200, resp.text
    chart = resp.json()["chart"]
    assert chart["type"] == "ESTJ"
    assert chart["answered"] == 32
    for d in chart["dimensions"]:
        assert d["left_pct"] == 100
        assert d["dominant"] == d["left_name"]


def test_pure_right_gives_infp() -> None:
    resp = client.post("/api/v1/charts/mbti", json={"options": {"answers": _answers(False)}})
    assert resp.status_code == 200, resp.text
    chart = resp.json()["chart"]
    assert chart["type"] == "INFP"
    for d in chart["dimensions"]:
        assert d["left_pct"] == 0


def test_neutral_answers_are_balanced() -> None:
    resp = client.post("/api/v1/charts/mbti", json={"options": {"answers": [3] * 32}})
    assert resp.status_code == 200, resp.text
    chart = resp.json()["chart"]
    for d in chart["dimensions"]:
        assert d["left_pct"] == 50
        assert d["strength"] == "轻微"


def test_requires_full_answers() -> None:
    resp = client.post("/api/v1/charts/mbti", json={"options": {"answers": [3] * 10}})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "engine_error"


def test_rejects_out_of_range() -> None:
    resp = client.post("/api/v1/charts/mbti", json={"options": {"answers": [9] * 32}})
    assert resp.status_code == 422
