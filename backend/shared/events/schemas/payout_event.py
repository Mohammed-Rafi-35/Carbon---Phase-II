from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PayoutCompletedPayload(BaseModel):
	transaction_id: UUID
	user_id: UUID
	claim_id: UUID | None = None
	amount: Decimal | None = None


class PayoutCompletedEvent(BaseModel):
	event_type: str = Field(default="PAYOUT_COMPLETED")
	event_id: UUID = Field(default_factory=uuid4)
	timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
	payload: PayoutCompletedPayload

