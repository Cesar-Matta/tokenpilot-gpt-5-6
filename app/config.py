"""Application configuration loaded exclusively from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Keep secrets outside source control."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    openai_api_key: str | None = None
    tokenpilot_api_keys: str = ""
    require_api_key: bool = False
    allowed_origins: str = ""
    request_rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    max_input_characters: int = Field(default=500_000, ge=1000)
    request_timeout_seconds: float = Field(default=90.0, ge=1.0, le=600.0)
    long_context_token_threshold: int = Field(default=128_000, ge=1_000)
    default_monthly_budget_usd: float | None = Field(default=None, ge=0)
    log_level: str = "INFO"

    @field_validator("environment")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.lower().strip()

    @property
    def api_keys(self) -> tuple[str, ...]:
        return tuple(key.strip() for key in self.tokenpilot_api_keys.split(",") if key.strip())

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
