from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AutoClaimRequest(BaseModel):
    user_id: UUID
    event_id: UUID


class AutoClaimData(BaseModel):
    claim_id: UUID
    status: str


class ProcessClaimRequest(BaseModel):
    claim_id: UUID


class ProcessClaimData(BaseModel):
    status: str
    payout_amount: Decimal | None = None


class ClaimHistoryItem(BaseModel):
    claim_id: UUID
    event_id: UUID
    status: str
    payout_amount: Decimal | None
    created_at: datetime


class ClaimLogItem(BaseModel):
    stage: str
    message: str
    timestamp: datetime
    details: dict[str, Any] | None = None


class ClaimDetailData(BaseModel):
    claim_id: UUID
    user_id: UUID
    policy_id: UUID | None = None
    event_id: UUID
    status: str
    risk_score: Decimal | None = None
    fraud_score: Decimal | None = None
    payout_amount: Decimal | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    logs: list[ClaimLogItem] = Field(default_factory=list)
