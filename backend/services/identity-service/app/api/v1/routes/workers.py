from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.worker import WorkerProfileData, WorkerProfileUpsertData, WorkerProfileUpsertRequest
from app.services.worker_service import WorkerService
from app.utils.responses import success_response


router = APIRouter(prefix="/workers", tags=["workers"])


@router.post("/profile", response_model=StandardResponse)
def create_or_update_profile(
    payload: WorkerProfileUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if payload.user_id != current_user.id:
        raise AppError("You can only update your own profile.", "FORBIDDEN", 403)

    service = WorkerService(db)
    profile = service.upsert_profile(
        user_id=payload.user_id,
        zone=payload.zone,
        vehicle_type=payload.vehicle_type,
        avg_weekly_income=payload.avg_weekly_income,
    )
    data = WorkerProfileUpsertData(profile_id=profile.id, status="created").model_dump()
    return success_response(data)


@router.get("/{user_id}", response_model=StandardResponse)
def get_worker_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    service = WorkerService(db)
    profile = service.get_profile_by_user_id(user_id)
    data = WorkerProfileData(
        user_id=profile.user_id,
        zone=profile.zone,
        avg_weekly_income=profile.avg_weekly_income,
        status=profile.status,
    ).model_dump()
    return success_response(data)
