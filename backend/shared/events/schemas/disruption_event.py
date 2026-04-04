from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DisruptionDetectedPayload(BaseModel):
	event_id: UUID
	zone: str
	severity: str
	type: str


class DisruptionDetectedEvent(BaseModel):
	event_type: str = Field(default="DISRUPTION_DETECTED")
	event_id: UUID = Field(default_factory=uuid4)
	timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
	payload: DisruptionDetectedPayload

