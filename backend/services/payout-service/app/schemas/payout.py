from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProcessPayoutRequest(BaseModel):
    claim_id: UUID
    user_id: UUID
    amount: Decimal = Field(gt=0)


class ProcessPayoutData(BaseModel):
    transaction_id: UUID
    status: str


class RetryPayoutRequest(BaseModel):
    transaction_id: UUID


class RetryPayoutData(BaseModel):
    status: str


class PayoutHistoryItem(BaseModel):
    transaction_id: UUID
    claim_id: UUID
    user_id: UUID
    amount: Decimal
    status: str
    timestamp: datetime
    processed_at: datetime | None
    transaction_ref: str | None
