from __future__ import annotations

from decimal import Decimal
from enum import StrEnum


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
BEARER_PREFIX = "Bearer "
ERROR_INVALID_AUTH_HEADER = "Authorization header is missing or invalid."

GST_PERCENT = Decimal("0.18")

ZONE_RATE_MAP: dict[str, Decimal] = {
	"LR-1": Decimal("0.015"),
	"MR-2": Decimal("0.025"),
	"HR-3": Decimal("0.040"),
}

COVERAGE_RATE_MAP: dict[str, Decimal] = {
	"LR-1": Decimal("0.60"),
	"MR-2": Decimal("0.70"),
	"HR-3": Decimal("0.80"),
}


class PolicyStatus(StrEnum):
	WAITING_PERIOD = "waiting_period"
	ACTIVE = "active"
	LAPSED = "lapsed"


class Role(StrEnum):
	ADMIN = "admin"
	WORKER = "worker"
	SERVICE = "service"
