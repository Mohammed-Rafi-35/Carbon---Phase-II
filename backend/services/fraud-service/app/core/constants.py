from __future__ import annotations

from enum import StrEnum


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
BEARER_PREFIX = "Bearer "
ERROR_INVALID_AUTH_HEADER = "Authorization header is missing or invalid."


class FraudStatus(StrEnum):
	PASS = "PASS"
	FAIL = "FAIL"


class FraudSource(StrEnum):
	API = "api"
	EVENT = "event"
	OVERRIDE = "override"

