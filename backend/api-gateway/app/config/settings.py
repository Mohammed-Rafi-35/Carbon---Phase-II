from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "API Gateway"
    app_env: str = "development"
    enforce_https: bool = False

    request_timeout_seconds: float = Field(default=15.0, ge=1.0, le=120.0)
    analytics_service_url: str = Field(default="http://analytics-service:8000")
    analytics_api_prefix: str = "/api/v1/analytics"
    identity_service_url: str = Field(default="http://identity-service:8000")
    identity_api_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
