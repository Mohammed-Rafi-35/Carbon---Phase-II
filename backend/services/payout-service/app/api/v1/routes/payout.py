from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    enforce_rate_limit,
    get_current_subject,
    get_db_session,
    get_idempotency_key,
    get_request_id,
    require_roles,
)
from app.core.exceptions import AppError
from app.schemas.common import StandardResponse
from app.schemas.payout import ProcessPayoutRequest, RetryPayoutRequest
from app.services.metrics_service import PAYOUT_PROCESSING_SECONDS
from app.services.payout_service import PayoutService
from app.utils.responses import success_response


router = APIRouter(prefix="/payout", tags=["payout"])


@router.post("/process", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
def process_payout(
    payload: ProcessPayoutRequest,
    idempotency_key: str = Depends(get_idempotency_key),
    _: str = Depends(get_request_id),
    __: str = Depends(require_roles("worker", "admin", "service")),
    ___: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = PayoutService(db)
    with PAYOUT_PROCESSING_SECONDS.time():
        result = service.process_payout(payload, idempotency_key=idempotency_key)
    return success_response(result.model_dump())


@router.get("/{user_id}", response_model=StandardResponse)
def get_payout_history(
    user_id: UUID,
    current_subject: UUID = Depends(get_current_subject),
    role: str = Depends(require_roles("worker", "admin", "service")),
    _: str = Depends(get_request_id),
    __: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    if role == "worker" and current_subject != user_id:
        raise AppError("Workers can view only their own payout history.", "FORBIDDEN", 403)

    service = PayoutService(db)
    history = service.get_payout_history(user_id)
    return success_response([item.model_dump() for item in history])


@router.post("/retry", response_model=StandardResponse)
def retry_failed_payout(
    payload: RetryPayoutRequest,
    _: str = Depends(get_request_id),
    __: str = Depends(require_roles("admin", "service")),
    ___: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = PayoutService(db)
    result = service.retry_failed_payout(payload.transaction_id)
    return success_response(result.model_dump())
