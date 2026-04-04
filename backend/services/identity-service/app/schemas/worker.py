from __future__ import annotations

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WorkerProfileUpsertRequest(BaseModel):
    user_id: UUID
    zone: str = Field(min_length=2, max_length=60)
    vehicle_type: Literal["bike", "cycle"]
    avg_weekly_income: Decimal = Field(gt=0)


class WorkerProfileUpsertData(BaseModel):
    profile_id: UUID
    status: str


class WorkerProfileData(BaseModel):
    user_id: UUID
    zone: str
    avg_weekly_income: Decimal
    status: str
