"""应用配置：全部来自环境变量，缺省即可本地跑通。"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SM_", extra="ignore")

    app_name: str = "suanming"
    debug: bool = False

    # CORS：开发期放行本地前端
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # LLM：OpenAI 兼容协议；未配置 key 时解读接口返回降级提示
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_timeout: float = 90.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
