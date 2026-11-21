from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _draw(**options):
    return client.post("/api/v1/charts/tarot", json={"options": options})


def test_tarot_three_card_spread_without_birth() -> None:
    resp = _draw(spread="three", seed=42)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chart"]["spread"] == "three"
    assert len(body["chart"]["cards"]) == 3
    assert [c["position"] for c in body["chart"]["cards"]] == ["过去", "现在", "未来"]
    for card in body["chart"]["cards"]:
        assert card["orientation"] in {"正位", "逆位"}
        assert card["keywords"]


def test_tarot_is_reproducible_with_seed() -> None:
    first = _draw(spread="celtic", seed=7).json()["chart"]["cards"]
    second = _draw(spread="celtic", seed=7).json()["chart"]["cards"]
    assert first == second
    assert len(first) == 10


def test_tarot_unknown_spread_422() -> None:
    resp = _draw(spread="nope")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "engine_error"


def test_tarot_cards_are_unique() -> None:
    cards = _draw(spread="five", seed=1).json()["chart"]["cards"]
    names = [c["name"] for c in cards]
    assert len(names) == len(set(names))


def test_tarot_text_renders() -> None:
    body = _draw(spread="single", seed=3, question="今年适合换工作吗").json()
    assert "塔罗牌阵" in body["text"]
    assert "今年适合换工作吗" in body["text"]
