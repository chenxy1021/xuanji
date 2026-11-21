"""统一错误模型。"""

from __future__ import annotations

from fastapi import HTTPException


class AppError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


class UnknownSystemError(AppError):
    def __init__(self, system: str) -> None:
        super().__init__("unknown_system", f"不支持的体系：{system}", 404)


class EngineError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("engine_error", message, 422)
