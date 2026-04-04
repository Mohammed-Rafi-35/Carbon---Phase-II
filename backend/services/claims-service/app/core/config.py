from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "Claims & Decision Service"
	app_env: str = "development"
	debug: bool = False
	api_v1_prefix: str = "/api/v1"
	enforce_https: bool = False

	database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5436/claims_db")
	database_connect_timeout_seconds: int = Field(default=5)
	auto_create_tables: bool = Field(default=False)

	rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672//")
	claims_exchange_name: str = Field(default="devtrails.events")
	claims_inbound_queue_name: str = Field(default="claims.disruption")
	claims_processing_queue_name: str = Field(default="claims.processing")
	claims_inbound_routing_key: str = Field(default="trigger.disruption_detected")
	claim_processing_routing_key: str = Field(default="claim.processing")
	claim_initiated_routing_key: str = Field(default="claim.initiated")
	claim_approved_routing_key: str = Field(default="claim.approved")
	enable_event_consumer: bool = Field(default=True)
	retry_limit: int = Field(default=3)
	prefetch_count: int = Field(default=10)

	jwt_secret: str = Field(default="change-me-in-production")
	jwt_algorithm: str = Field(default="HS256")
	rate_limit_per_minute: int = Field(default=60)

	policy_service_url: str = Field(default="http://policy-pricing-service:8000")
	ai_service_url: str = Field(default="http://ai-risk-service:8000")
	fraud_service_url: str = Field(default="http://fraud-service:8000")
	payout_service_url: str = Field(default="http://payout-service:8000")
	integration_timeout_seconds: float = Field(default=5.0)
	risk_reject_threshold: float = Field(default=0.95)
	risk_default_zone: str = Field(default="UNKNOWN")

	default_claim_users_csv: str = Field(default="16fd2706-8baf-433b-82eb-8c7fada847da")
	default_payout_amount: float = Field(default=500.0)

	@property
	def default_claim_users(self) -> list[str]:
		return [item.strip() for item in self.default_claim_users_csv.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
	return Settings()

