from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "Payout Service"
	app_env: str = "development"
	debug: bool = False
	api_v1_prefix: str = "/api/v1"
	enforce_https: bool = False

	database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5434/payout_db")
	database_connect_timeout_seconds: int = Field(default=5)
	auto_create_tables: bool = Field(default=False)

	jwt_secret: str = Field(default="change-me-in-production")
	jwt_algorithm: str = Field(default="HS256")
	rate_limit_per_minute: int = Field(default=60)

	payment_provider: str = Field(default="mock")
	payment_gateway_api_key: str = Field(default="")
	payment_gateway_secret: str = Field(default="")
	payment_timeout_seconds: int = Field(default=10)
	mock_gateway_force_failure: bool = Field(default=False)

	max_retry: int = Field(default=3)

	enable_event_publish: bool = Field(default=False)
	rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672//")
	enable_event_consumer: bool = Field(default=True)
	payout_inbound_queue_name: str = Field(default="payout.claims")
	claim_approved_event_routing_key: str = Field(default="claim.approved")
	retry_limit: int = Field(default=3)
	prefetch_count: int = Field(default=10)
	payout_completed_event_routing_key: str = Field(default="payout.completed")
	payout_failed_event_routing_key: str = Field(default="payout.failed")


@lru_cache
def get_settings() -> Settings:
	return Settings()

