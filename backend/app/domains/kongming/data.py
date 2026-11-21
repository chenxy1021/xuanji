"""孔明神卦的静态数据：康熙笔画表、简繁折算表、384 签。

数据来源见同目录 NOTICE.md。
"""

from __future__ import annotations

import gzip
import json
from functools import lru_cache
from importlib.resources import files
from typing import Any


@lru_cache(maxsize=1)
def _load_kangxi() -> tuple[dict[str, int], dict[str, str]]:
    path = files(__package__) / "data" / "kangxi.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload["strokes"], payload["trad"]


@lru_cache(maxsize=1)
def _load_lots() -> dict[int, dict[str, Any]]:
    path = files(__package__) / "data" / "lots.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return {row["number"]: row for row in json.load(fh)}


def strokes() -> dict[str, int]:
    return _load_kangxi()[0]


def traditional_map() -> dict[str, str]:
    return _load_kangxi()[1]


def lot(number: int) -> dict[str, Any] | None:
    return _load_lots().get(number)


def lot_count() -> int:
    return len(_load_lots())
