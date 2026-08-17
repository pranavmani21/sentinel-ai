"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SentinelAI API"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel",
        repr=False,
    )
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""

    return Settings()

