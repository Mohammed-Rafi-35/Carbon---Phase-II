from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import enforce_rate_limit, get_db_session, get_request_id, get_token_payload
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.schemas.trigger import StopTriggerRequest, TriggerMockRequest
from app.services.trigger_service import TriggerService
from app.utils.responses import success_response


router = APIRouter(prefix="/trigger", tags=["Trigger"])


@router.post(
    "/mock",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)],
)
def trigger_mock_event(
    payload: TriggerMockRequest,
    _: dict = Depends(get_token_payload),
    __: str = Depends(get_request_id),
    db: Session = Depends(get_db_session),
) -> dict:
    settings = get_settings()
    if not settings.enable_manual_trigger:
        raise AppError(
            "Manual trigger endpoint is disabled. Use scheduler-driven detection.",
            "MANUAL_TRIGGER_DISABLED",
            403,
        )

    service = TriggerService(db=db)
    disruption = service.create_manual_trigger(
        zone=payload.zone,
        disruption_type=payload.type.value,
        severity=payload.severity.value,
    )
    return success_response({"event_id": disruption.id, "status": "triggered"})


@router.get("/active", status_code=status.HTTP_200_OK)
def get_active_triggers(
    _: dict = Depends(get_token_payload),
    __: str = Depends(get_request_id),
    db: Session = Depends(get_db_session),
) -> dict:
    service = TriggerService(db=db)
    active = service.get_active_disruptions()

    data = [
        {
            "event_id": item.id,
            "zone": item.zone,
            "type": item.type,
            "severity": item.severity,
            "start_time": item.start_time,
        }
        for item in active
    ]
    return success_response(data)


@router.post("/stop", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit)])
def stop_trigger(
    payload: StopTriggerRequest,
    _: dict = Depends(get_token_payload),
    __: str = Depends(get_request_id),
    db: Session = Depends(get_db_session),
) -> dict:
    service = TriggerService(db=db)
    service.stop_trigger(event_id=str(payload.event_id))
    return success_response({"status": "stopped"})
