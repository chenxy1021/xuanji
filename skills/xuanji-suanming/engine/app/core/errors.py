"""统一错误模型（技能内 CLI 版：不依赖 FastAPI）。"""

from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.detail = {"code": code, "message": message}
        self.status_code = status_code


class UnknownSystemError(AppError):
    def __init__(self, system: str) -> None:
        super().__init__("unknown_system", f"不支持的体系：{system}", 404)


class EngineError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("engine_error", message, 422)
