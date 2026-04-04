from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.worker_profile import WorkerProfile


class WorkerProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: UUID) -> WorkerProfile | None:
        return self.db.scalar(select(WorkerProfile).where(WorkerProfile.user_id == user_id))

    def upsert_profile(
        self,
        *,
        user_id: UUID,
        zone: str,
        vehicle_type: str,
        avg_weekly_income: Decimal,
    ) -> WorkerProfile:
        profile = self.get_by_user_id(user_id)
        if profile:
            profile.zone = zone
            profile.vehicle_type = vehicle_type
            profile.avg_weekly_income = avg_weekly_income
            profile.status = "active"
        else:
            profile = WorkerProfile(
                user_id=user_id,
                zone=zone,
                vehicle_type=vehicle_type,
                avg_weekly_income=avg_weekly_income,
                status="active",
            )
            self.db.add(profile)

        self.db.commit()
        self.db.refresh(profile)
        return profile
