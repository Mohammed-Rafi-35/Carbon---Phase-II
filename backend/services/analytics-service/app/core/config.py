from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Analytics Service"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    enforce_https: bool = False

    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5440/analytics_db")
    database_connect_timeout_seconds: int = Field(default=5)
    auto_create_tables: bool = Field(default=False)

    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672//")
    redis_url: str | None = Field(default="redis://localhost:6379/0")
    analytics_exchange_name: str = Field(default="devtrails.events")
    analytics_event_queue_name: str = Field(default="analytics.events")
    analytics_event_routing_key: str = Field(default="#")
    enable_event_consumer: bool = Field(default=True)
    retry_limit: int = Field(default=3)
    prefetch_count: int = Field(default=10)

    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    rate_limit_per_minute: int = Field(default=120)

    cache_ttl_seconds: int = Field(default=300)
    dashboard_cache_ttl_seconds: int = Field(default=60)
    zones_cache_ttl_seconds: int = Field(default=120)
    timeseries_cache_ttl_seconds: int = Field(default=120)
    default_lookback_days: int = Field(default=30)


@lru_cache
def get_settings() -> Settings:
    return Settings()
