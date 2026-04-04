from __future__ import annotations

from enum import StrEnum


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
BEARER_PREFIX = "Bearer "
ERROR_INVALID_AUTH_HEADER = "Authorization header is missing or invalid."


class Role(StrEnum):
    ADMIN = "admin"
    WORKER = "worker"
    SERVICE = "service"


class EventType(StrEnum):
    DISRUPTION_DETECTED = "DISRUPTION_DETECTED"
    CLAIM_INITIATED = "CLAIM_INITIATED"
    CLAIM_APPROVED = "CLAIM_APPROVED"
    FRAUD_DETECTED = "FRAUD_DETECTED"
    PAYOUT_COMPLETED = "PAYOUT_COMPLETED"
    POLICY_CREATED = "POLICY_CREATED"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TimeSeriesMetric(StrEnum):
    CLAIMS = "claims"
    PAYOUT = "payout"
    FRAUD = "fraud"
    POLICY = "policy"
    DISRUPTION = "disruption"
    ACTIVE_USERS = "active_users"
