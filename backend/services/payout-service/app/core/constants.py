from __future__ import annotations

from enum import StrEnum


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
IDEMPOTENCY_KEY_HEADER_NAME = "Idempotency-Key"
BEARER_PREFIX = "Bearer "
ERROR_INVALID_AUTH_HEADER = "Authorization header is missing or invalid."


class Role(StrEnum):
	ADMIN = "admin"
	WORKER = "worker"
	SERVICE = "service"


class PayoutStatus(StrEnum):
	PENDING = "pending"
	COMPLETED = "completed"
	FAILED = "failed"


class LedgerEntryType(StrEnum):
	CREDIT = "credit"

