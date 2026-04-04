from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "Policy & Pricing Service"
	app_env: str = "development"
	debug: bool = False
	api_v1_prefix: str = "/api/v1"
	enforce_https: bool = False

	database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5433/policy_pricing_db")
	database_connect_timeout_seconds: int = Field(default=5)

	rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672//")
	redis_url: str | None = Field(default="redis://localhost:6379/0")

	jwt_secret: str = Field(default="change-me-in-production")
	jwt_algorithm: str = Field(default="HS256")

	gst_rate: float = Field(default=0.18)
	waiting_period_hours: int = Field(default=48)

	rate_limit_per_minute: int = Field(default=60)
	integration_timeout_seconds: float = Field(default=5.0)

	identity_service_url: str = Field(default="http://identity-service:8000")
	fraud_service_url: str = Field(default="http://fraud-service:8000")
	claims_service_url: str = Field(default="http://claims-service:8000")
	ai_risk_service_url: str = Field(default="http://ai-risk-service:8000")

	auto_create_tables: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
	return Settings()
