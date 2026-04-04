from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "Identity & Worker Service"
	app_env: str = "development"
	debug: bool = False
	api_v1_prefix: str = "/api/v1"
	enforce_https: bool = False

	database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/identity_db")
	database_connect_timeout_seconds: int = Field(default=5)
	enable_dev_sqlite_fallback: bool = Field(default=False)
	dev_sqlite_fallback_url: str = Field(default="sqlite:///./identity_dev.db")

	jwt_secret: str = Field(default="change-me-in-production")
	jwt_algorithm: str = Field(default="HS256")
	jwt_expiry: int = Field(default=3600)
	jwt_issuer: str = Field(default="identity-service")
	refresh_token_expiry_days: int = Field(default=14)

	redis_url: str | None = Field(default=None)

	integration_timeout_seconds: float = Field(default=5.0)
	policy_service_url: str = Field(default="http://policy-pricing-service:8001")
	claims_service_url: str = Field(default="http://claims-service:8002")

	auto_create_tables: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
	return Settings()

