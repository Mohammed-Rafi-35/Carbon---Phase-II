from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ClaimInitiatedPayload(BaseModel):
	claim_id: UUID
	user_id: UUID
	event_id: UUID | None = None


class ClaimApprovedPayload(BaseModel):
	claim_id: UUID
	amount: Decimal
	user_id: UUID | None = None


class ClaimInitiatedEvent(BaseModel):
	event_type: str = Field(default="CLAIM_INITIATED")
	event_id: UUID = Field(default_factory=uuid4)
	timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
	payload: ClaimInitiatedPayload


class ClaimApprovedEvent(BaseModel):
	event_type: str = Field(default="CLAIM_APPROVED")
	event_id: UUID = Field(default_factory=uuid4)
	timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
	payload: ClaimApprovedPayload

