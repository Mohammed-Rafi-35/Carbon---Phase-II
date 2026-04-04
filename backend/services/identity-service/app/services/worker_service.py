from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.worker_profile import WorkerProfile
from app.repositories.user_repository import UserRepository
from app.repositories.worker_profile_repository import WorkerProfileRepository


class WorkerService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)
        self.worker_repo = WorkerProfileRepository(db)

    def upsert_profile(
        self,
        user_id: UUID,
        zone: str,
        vehicle_type: str,
        avg_weekly_income: Decimal,
    ) -> WorkerProfile:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AppError("User not found.", "USER_NOT_FOUND", 404)

        return self.worker_repo.upsert_profile(
            user_id=user_id,
            zone=zone,
            vehicle_type=vehicle_type,
            avg_weekly_income=avg_weekly_income,
        )

    def get_profile_by_user_id(self, user_id: UUID) -> WorkerProfile:
        profile = self.worker_repo.get_by_user_id(user_id)
        if not profile:
            raise AppError("Worker profile not found.", "PROFILE_NOT_FOUND", 404)
        return profile
