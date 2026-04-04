from __future__ import annotations

from enum import StrEnum


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
BEARER_PREFIX = "Bearer "
ERROR_INVALID_AUTH_HEADER = "Authorization header is missing or invalid."

BASE_FEATURE_NAMES: list[str] = [
	"disruption_freq",
	"duration",
	"traffic",
	"order_drop",
	"activity",
	"claims",
]

MODEL_FEATURE_NAMES: list[str] = [
	"disruption_freq",
	"duration",
	"traffic",
	"order_drop",
	"activity",
	"claims",
	"disruption_traffic_interaction",
	"exposure_index",
	"resilience_gap",
	"rolling_disruption_3h",
	"traffic_lag_1",
	"previous_risk_score",
	"risk_trend_1h",
]

RISK_CLASSIFICATION_STRATEGY = "thresholds"


class RiskCategory(StrEnum):
	LOW = "LOW"
	MEDIUM = "MEDIUM"
	HIGH = "HIGH"
