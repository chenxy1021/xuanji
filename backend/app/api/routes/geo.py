"""地理数据路由。"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.types import Place
from app.domains.shared.cities import search_cities

router = APIRouter(tags=["geo"])


@router.get("/geo/cities", response_model=list[Place], summary="城市检索（含经纬度）")
def cities(q: str = "", limit: int = Query(default=20, ge=1, le=100)) -> list[Place]:
    return search_cities(q, limit)
