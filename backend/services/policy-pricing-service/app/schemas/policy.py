from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import COVERAGE_RATE_MAP, ZONE_RATE_MAP


class CreatePolicyRequest(BaseModel):
    user_id: UUID
    weekly_income: Decimal = Field(gt=0)
    zone: str | None = None
    activity_days: int | None = Field(default=None, ge=0, le=7)
    policy_week: int = Field(default=1, ge=1)
    premium_paid: bool = True
    fraud_flag: bool = False

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in ZONE_RATE_MAP:
            raise ValueError(f"zone must be one of: {', '.join(ZONE_RATE_MAP.keys())}")
        return value


class PolicyResponseData(BaseModel):
    policy_id: UUID
    user_id: UUID
    premium: Decimal
    start_date: datetime
    iwi: Decimal
    idi: Decimal
    zone: str
    coverage_rate: Decimal
    base_premium: Decimal
    stabilization_factor: Decimal
    gst: Decimal
    total_premium: Decimal
    waiting_period_end: datetime
    status: str
    activity_days: int


class ValidatePolicyRequest(BaseModel):
    user_id: UUID
    policy_id: UUID


class ValidatePolicyData(BaseModel):
    valid: bool
    reason: str | None = None


class CalculatePremiumRequest(BaseModel):
    weekly_income: Decimal = Field(gt=0)
    zone: str
    policy_week: int = Field(default=1, ge=1)
    risk_multiplier: Decimal = Field(default=Decimal("1.0"), gt=0)

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, value: str) -> str:
        if value not in ZONE_RATE_MAP:
            raise ValueError(f"zone must be one of: {', '.join(ZONE_RATE_MAP.keys())}")
        return value


class PremiumBreakdownData(BaseModel):
    weekly_income: Decimal
    zone: str
    zone_rate: Decimal
    coverage_rate: Decimal
    stabilization_factor: Decimal
    risk_multiplier: Decimal
    base_premium: Decimal
    gst: Decimal
    total_premium: Decimal


class WorkerProfileData(BaseModel):
    user_id: UUID
    zone: str
    avg_weekly_income: Decimal | None = None
    status: str | None = None

    @field_validator("zone")
    @classmethod
    def validate_worker_zone(cls, value: str) -> str:
        if value not in COVERAGE_RATE_MAP:
            raise ValueError("Unsupported zone from identity service.")
        return value