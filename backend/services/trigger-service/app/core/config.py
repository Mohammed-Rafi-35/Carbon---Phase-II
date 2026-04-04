from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "Trigger Service"
	app_env: str = "development"
	debug: bool = False
	api_v1_prefix: str = "/api/v1"
	enforce_https: bool = False

	database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5434/trigger_db")
	database_connect_timeout_seconds: int = Field(default=5)

	rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672//")
	trigger_exchange_name: str = Field(default="devtrails.events")
	trigger_routing_key: str = Field(default="trigger.disruption_detected")

	jwt_secret: str = Field(default="change-me-in-production")
	jwt_algorithm: str = Field(default="HS256")

	rate_limit_per_minute: int = Field(default=60)

	integration_timeout_seconds: float = Field(default=5.0)
	poll_interval_seconds: int = Field(default=300)
	scheduler_lock_key: int = Field(default=42042)
	poll_zones_csv: str = Field(default="MR-2")
	weather_api_url: str = Field(default="https://api.open-meteo.com/v1/forecast")
	traffic_api_url: str | None = Field(default=None)
	platform_api_url: str | None = Field(default=None)

	threshold_rain: float = Field(default=50.0)
	threshold_traffic: float = Field(default=0.7)
	threshold_platform_outage: float = Field(default=0.5)

	enable_scheduler: bool = Field(default=True)
	enable_manual_trigger: bool = Field(default=False)
	auto_create_tables: bool = Field(default=False)

	@property
	def poll_zones(self) -> list[str]:
		return [zone.strip() for zone in self.poll_zones_csv.split(",") if zone.strip()]


@lru_cache
def get_settings() -> Settings:
	return Settings()
