from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TriggerType(StrEnum):
    WEATHER = "weather"
    TRAFFIC = "traffic"
    PLATFORM = "platform"


class TriggerSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TriggerMockRequest(BaseModel):
    zone: str = Field(min_length=1, max_length=128)
    type: TriggerType
    severity: TriggerSeverity


class StopTriggerRequest(BaseModel):
    event_id: UUID


class ActiveTriggerItem(BaseModel):
    event_id: UUID
    zone: str
    type: TriggerType
    severity: TriggerSeverity
    start_time: datetime


class TriggerMockResponseData(BaseModel):
    event_id: UUID
    status: Literal["triggered"]


class StopTriggerResponseData(BaseModel):
    status: Literal["stopped"]


class DisruptionEventPayload(BaseModel):
    event: Literal["DISRUPTION_DETECTED"]
    event_id: UUID
    zone: str
    type: TriggerType
    severity: TriggerSeverity
    timestamp: datetime
