from __future__ import annotations

from enum import StrEnum


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
BEARER_PREFIX = "Bearer "


class NotificationChannel(StrEnum):
	SMS = "SMS"
	PUSH = "PUSH"
	IN_APP = "IN_APP"


class NotificationType(StrEnum):
	CLAIM_UPDATE = "CLAIM_UPDATE"
	PAYOUT = "PAYOUT"
	POLICY = "POLICY"


class NotificationStatus(StrEnum):
	QUEUED = "queued"
	SENT = "sent"
	FAILED = "failed"
	RETRY_SCHEDULED = "retry_scheduled"


ERROR_INVALID_AUTH_HEADER = "Authorization header is missing or invalid."
