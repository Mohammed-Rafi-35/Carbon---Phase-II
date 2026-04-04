from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    enforce_rate_limit,
    get_current_subject,
    get_authorization_header,
    get_db_session,
    get_request_id,
    require_admin_role,
)
from app.schemas.common import StandardResponse
from app.schemas.fraud import FraudCheckRequest, FraudOverrideRequest
from app.services.fraud_service import FraudService
from app.utils.responses import success_response


router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post("/check", response_model=StandardResponse)
def fraud_check(
    payload: FraudCheckRequest,
    token: str = Depends(get_authorization_header),
    request_id: str = Depends(get_request_id),
    ___: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = FraudService(db)
    result = service.check_claim(payload, source="api", token=token, request_id=request_id)
    return success_response(result.model_dump())


@router.post("/override", response_model=StandardResponse)
def manual_override(
    payload: FraudOverrideRequest,
    _: str = Depends(get_authorization_header),
    __: str = Depends(get_request_id),
    ___: str = Depends(require_admin_role),
    admin_subject: str = Depends(get_current_subject),
    ____: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = FraudService(db)
    result = service.override_claim(payload, admin_subject=admin_subject)
    return success_response(result.model_dump())


@router.get("/{claim_id}", response_model=StandardResponse)
def get_fraud_log(
    claim_id: UUID,
    _: str = Depends(get_authorization_header),
    __: str = Depends(get_request_id),
    ___: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = FraudService(db)
    result = service.get_claim_log(claim_id)
    return success_response(result.model_dump(mode="json"))
