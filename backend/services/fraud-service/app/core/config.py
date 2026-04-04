from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "Fraud Detection Service"
	app_env: str = "development"
	debug: bool = False
	api_v1_prefix: str = "/api/v1"
	enforce_https: bool = False

	database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5437/fraud_db")
	database_connect_timeout_seconds: int = Field(default=5)
	auto_create_tables: bool = Field(default=False)

	rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672//")
	fraud_exchange_name: str = Field(default="devtrails.events")
	fraud_inbound_queue_name: str = Field(default="fraud.claims")
	fraud_inbound_routing_key: str = Field(default="claim.initiated")
	fraud_detected_routing_key: str = Field(default="fraud.detected")
	enable_event_consumer: bool = Field(default=True)
	retry_limit: int = Field(default=3)
	prefetch_count: int = Field(default=10)

	jwt_secret: str = Field(default="change-me-in-production")
	jwt_algorithm: str = Field(default="HS256")
	rate_limit_per_minute: int = Field(default=60)

	fraud_fail_threshold: float = Field(default=0.70)
	max_duplicate_claims: int = Field(default=1)
	enable_ml: bool = Field(default=False)
	model_path: str = Field(default="")

	integration_timeout_seconds: float = Field(default=5.0, ge=0.5, le=60.0)
	identity_service_url: str = Field(default="http://identity-service:8000")
	ai_risk_service_url: str = Field(default="http://ai-risk-service:8000")


@lru_cache
def get_settings() -> Settings:
	return Settings()

