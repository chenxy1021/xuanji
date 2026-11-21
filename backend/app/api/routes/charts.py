"""排盘相关路由。"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import AppError
from app.core.types import ChartEnvelope, ChartRequest, SystemSpec
from app.domains import get_domain, list_specs

router = APIRouter(tags=["charts"])


@router.get("/systems", response_model=list[SystemSpec], summary="体系清单")
def list_systems() -> list[SystemSpec]:
    return list_specs()


@router.post("/charts/{system}", response_model=ChartEnvelope, summary="排盘")
def create_chart(system: str, payload: ChartRequest) -> ChartEnvelope:
    domain = get_domain(system)
    if domain.SPEC.requires_birth and payload.birth is None:
        raise AppError("missing_birth", "该体系需要出生信息", 422)
    if domain.SPEC.requires_secondary and payload.secondary is None:
        raise AppError("missing_secondary", "合盘需要提供第二个人的出生信息", 422)

    options = dict(payload.options)
    if payload.secondary is not None:
        options["secondary"] = payload.secondary
    return domain.compute(payload.birth, options)
