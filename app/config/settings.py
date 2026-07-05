from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "my-agent"
    app_env: str = "local"
    app_debug: bool = True
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/my_agent"
    redis_url: str = "redis://localhost:6379/0"
    default_model_provider: str = "openai"
    default_model_name: str = "gpt-4.1-mini"
    max_agent_steps: int = Field(default=8, ge=1)
    request_timeout_seconds: int = Field(default=60, ge=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
