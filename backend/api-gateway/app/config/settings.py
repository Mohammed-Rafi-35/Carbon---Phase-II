from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "API Gateway"
    app_env: str = "development"
    enforce_https: bool = False

    request_timeout_seconds: float = Field(default=3.0, ge=1.0, le=120.0)
    upstream_retry_attempts: int = Field(default=2, ge=1, le=5)
    upstream_retry_backoff_seconds: float = Field(default=0.1, ge=0.0, le=5.0)
    circuit_breaker_failure_threshold: int = Field(default=5, ge=1, le=100)
    circuit_breaker_open_seconds: float = Field(default=30.0, ge=1.0, le=600.0)

    max_request_body_bytes: int = Field(default=1_048_576, ge=1_024, le=20_971_520)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10_000)

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    cors_allow_origins_csv: str = "http://localhost:3000"
    auth_exempt_paths_csv: str = "/health,/docs,/redoc,/openapi.json,/api/v1/auth"

    analytics_service_url: str = Field(default="http://analytics-service:8000")
    analytics_api_prefix: str = "/api/v1/analytics"
    identity_service_url: str = Field(default="http://identity-service:8000")
    identity_api_prefix: str = "/api/v1"
    claims_service_url: str = Field(default="http://claims-service:8000")
    claims_api_prefix: str = "/api/v1"
    policy_service_url: str = Field(default="http://policy-pricing-service:8000")
    policy_api_prefix: str = "/api/v1"
    fraud_service_url: str = Field(default="http://fraud-service:8000")
    fraud_api_prefix: str = "/api/v1"
    payout_service_url: str = Field(default="http://payout-service:8000")
    payout_api_prefix: str = "/api/v1"
    ai_service_url: str = Field(default="http://ai-risk-service:8000")
    ai_api_prefix: str = "/api/v1"
    notification_service_url: str = Field(default="http://notification-service:8000")
    notification_api_prefix: str = "/api/v1"
    trigger_service_url: str = Field(default="http://trigger-service:8000")
    trigger_api_prefix: str = "/api/v1"

    @property
    def cors_allow_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_allow_origins_csv.split(",") if origin.strip()]

    @property
    def auth_exempt_paths(self) -> List[str]:
        return [path.strip() for path in self.auth_exempt_paths_csv.split(",") if path.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
