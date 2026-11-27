"""领域注册表：按需加载，没装的体系不影响其他体系。"""

from __future__ import annotations

import importlib
from types import ModuleType

from app.core.errors import UnknownSystemError
from app.core.types import SystemSpec

DOMAINS: dict[str, str] = {
    "bazi": ".bazi.api",
    "ziwei": ".ziwei.api",
    "astrology": ".astrology.api",
    "qimen": ".qimen.api",
    "bazi_hepan": ".bazi_hepan.api",
    "ziwei_hepan": ".ziwei_hepan.api",
    "liuyao": ".liuyao.api",
    "tarot": ".tarot.api",
    "meihua": ".meihua.api",
    "kongming": ".kongming.api",
    "mbti": ".mbti.api",
}


def list_specs() -> list[SystemSpec]:
    specs: list[SystemSpec] = []
    for system in DOMAINS:
        try:
            specs.append(get_domain(system).SPEC)
        except Exception:  # noqa: BLE001 - 缺依赖的体系在列表里跳过
            continue
    return specs


def get_domain(system: str) -> ModuleType:
    try:
        module = DOMAINS[system]
    except KeyError as exc:
        raise UnknownSystemError(system) from exc
    return importlib.import_module(module, __package__)
