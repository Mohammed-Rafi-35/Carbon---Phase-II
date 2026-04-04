from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "AI Risk Service"
	app_env: str = "development"
	debug: bool = False
	api_v1_prefix: str = "/api/v1"
	enforce_https: bool = False
	database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5438/ai_risk_db")
	database_connect_timeout_seconds: int = Field(default=5)

	jwt_secret: str = Field(default="change-me-in-production")
	jwt_algorithm: str = Field(default="HS256")

	model_path: str = Field(default="ml/models/risk_model_v1.pkl")
	model_registry_path: str = Field(default="ml/models/model_registry.json")
	metadata_path: str = Field(default="ml/models/metadata.json")
	model_version: str = Field(default="v1")
	default_risk_score: float = Field(default=0.5)
	timeout_ms: int = Field(default=100)

	low_risk_threshold: float = Field(default=0.34)
	high_risk_threshold: float = Field(default=0.67)
	premium_multiplier_base: float = Field(default=1.0)
	premium_multiplier_sensitivity: float = Field(default=0.3)
	premium_multiplier_cap: float = Field(default=1.5)

	rate_limit_per_minute: int = Field(default=120)

	enable_external_signals: bool = Field(default=False)
	external_signal_timeout_seconds: float = Field(default=1.5)


@lru_cache
def get_settings() -> Settings:
	return Settings()
