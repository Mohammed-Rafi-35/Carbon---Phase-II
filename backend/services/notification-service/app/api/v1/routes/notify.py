from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import enforce_rate_limit, get_current_subject, get_db_session, get_request_id
from app.schemas.common import StandardResponse
from app.schemas.notification import NotificationRetryRequest, NotificationSendRequest
from app.services.notification_service import NotificationService
from app.utils.responses import success_response


router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("/send", response_model=StandardResponse, status_code=status.HTTP_202_ACCEPTED)
def send_notification(
    payload: NotificationSendRequest,
    _: UUID = Depends(get_current_subject),
    __: str = Depends(get_request_id),
    ___: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = NotificationService(db)
    ids = service.queue_notification(payload)

    if len(ids) == 1:
        data = {
            "notification_id": ids[0],
            "status": "queued",
        }
    else:
        data = {
            "notification_ids": ids,
            "status": "queued",
        }
    return success_response(data)


@router.get("/{user_id}", response_model=StandardResponse)
def get_notification_history(
    user_id: UUID,
    _: UUID = Depends(get_current_subject),
    __: str = Depends(get_request_id),
    ___: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = NotificationService(db)
    history = service.list_notification_history(user_id)
    return success_response([item.model_dump() for item in history])


@router.post("/retry", response_model=StandardResponse)
def retry_notification(
    payload: NotificationRetryRequest,
    _: UUID = Depends(get_current_subject),
    __: str = Depends(get_request_id),
    ___: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = NotificationService(db)
    service.retry_notification(payload.notification_id)
    return success_response({"status": "retry_scheduled"})
