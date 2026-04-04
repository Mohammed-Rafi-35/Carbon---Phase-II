from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class FraudActivity(BaseModel):
    gps_valid: bool = True
    activity_score: float = Field(default=1.0, ge=0.0, le=1.0)
    device_consistency: bool | None = None


class FraudEventContext(BaseModel):
    zone: str | None = Field(default=None, min_length=1, max_length=120)
    type: str | None = Field(default=None, min_length=1, max_length=40)
    severity: str | None = Field(default=None, min_length=1, max_length=20)


class FraudCheckRequest(BaseModel):
    claim_id: UUID
    user_id: UUID
    activity: FraudActivity = Field(default_factory=FraudActivity)
    event: FraudEventContext | None = None


class FraudCheckData(BaseModel):
    fraud_score: float
    status: str
    reason: str | None = None


class FraudLogData(BaseModel):
    claim_id: UUID
    user_id: UUID
    fraud_score: float
    status: str
    reason: str | None = None
    source: str
    timestamp: datetime


class FraudOverrideRequest(BaseModel):
    claim_id: UUID
    override_status: Literal["PASS", "FAIL"]
    reason: str = Field(min_length=3, max_length=255)


class FraudOverrideData(BaseModel):
    status: str
    claim_id: UUID
    override_status: str
