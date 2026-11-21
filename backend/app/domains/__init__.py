"""领域注册表：新增体系只需在此登记一行。

上线清单见 README。daily / monthly / xiaoliuren / daliuren 的代码仍在仓库中，
但不在本期范围，因此不注册、不对外提供接口。
"""

from __future__ import annotations

from types import ModuleType

from app.core.errors import UnknownSystemError
from app.core.types import SystemSpec

from .astrology import api as astrology_api
from .bazi import api as bazi_api
from .bazi_hepan import api as bazi_hepan_api
from .kongming import api as kongming_api
from .liuyao import api as liuyao_api
from .mbti import api as mbti_api
from .meihua import api as meihua_api
from .qimen import api as qimen_api
from .tarot import api as tarot_api
from .ziwei import api as ziwei_api
from .ziwei_hepan import api as ziwei_hepan_api

DOMAINS: dict[str, ModuleType] = {
    module.SPEC.id: module
    for module in (
        bazi_api,
        ziwei_api,
        astrology_api,
        qimen_api,
        bazi_hepan_api,
        ziwei_hepan_api,
        liuyao_api,
        tarot_api,
        meihua_api,
        kongming_api,
        mbti_api,
    )
}


def list_specs() -> list[SystemSpec]:
    return [module.SPEC for module in DOMAINS.values()]


def get_domain(system: str) -> ModuleType:
    try:
        return DOMAINS[system]
    except KeyError as exc:
        raise UnknownSystemError(system) from exc
