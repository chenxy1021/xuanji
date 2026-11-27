"""塔罗抽牌。

抽牌本身是随机的，但支持 `seed` 以便复现与测试；同一 seed + 同一牌阵得到同一结果。
"""

from __future__ import annotations

import random
from typing import Any

from app.core.errors import EngineError

from .deck import DECK, SPREADS

ENGINE_VERSION = "tarot-1.0"


def compute(options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    spread_key = str(options.get("spread") or "three")
    if spread_key not in SPREADS:
        raise EngineError(f"未知牌阵：{spread_key}")

    spread = SPREADS[spread_key]
    positions: list[str] = list(spread["positions"])  # type: ignore[arg-type]

    seed = options.get("seed")
    rng = random.Random(seed) if seed is not None else random.SystemRandom()

    cards = rng.sample(DECK, len(positions))
    drawn = []
    for position, card in zip(positions, cards, strict=True):
        reversed_flag = rng.random() < 0.4
        drawn.append(
            {
                "position": position,
                "name": card.name,
                "arcana": card.arcana,
                "suit": card.suit,
                "orientation": "逆位" if reversed_flag else "正位",
                "keywords": card.reversed if reversed_flag else card.upright,
            }
        )

    return {
        "engine": ENGINE_VERSION,
        "spread": spread_key,
        "spread_name": spread["name"],
        "spread_description": spread["description"],
        "question": (options.get("question") or "").strip(),
        "seed": seed,
        "cards": drawn,
    }
