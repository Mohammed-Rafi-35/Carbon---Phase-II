from __future__ import annotations

from enum import StrEnum


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
BEARER_PREFIX = "Bearer "
ERROR_INVALID_AUTH_HEADER = "Authorization header is missing or invalid."


class DisruptionStatus(StrEnum):
	ACTIVE = "active"
	STOPPED = "stopped"


class DisruptionSource(StrEnum):
	MANUAL = "manual"
	WEATHER = "weather_api"
	TRAFFIC = "traffic_api"
	PLATFORM = "platform_api"


class TriggerEventName(StrEnum):
	DISRUPTION_DETECTED = "DISRUPTION_DETECTED"

