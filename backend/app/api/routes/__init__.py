"""路由聚合。"""

from fastapi import APIRouter

from . import auth, charts, focus, geo, interpret, meta, quizzes, records, settings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(charts.router)
api_router.include_router(focus.router)
api_router.include_router(geo.router)
api_router.include_router(interpret.router)
api_router.include_router(meta.router)
api_router.include_router(quizzes.router)
api_router.include_router(records.router)
api_router.include_router(settings.router)

__all__ = ["api_router"]
