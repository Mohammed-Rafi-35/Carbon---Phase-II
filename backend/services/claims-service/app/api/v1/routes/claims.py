from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    enforce_rate_limit,
    get_authorization_header,
    get_current_subject,
    get_db_session,
    get_idempotency_key,
    get_request_id,
    require_roles,
)
from app.core.exceptions import AppError
from app.schemas.claims import AutoClaimRequest, ProcessClaimRequest
from app.schemas.common import StandardResponse
from app.services.claim_service import ClaimService
from app.utils.responses import success_response


router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/auto", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
def auto_create_claim(
    payload: AutoClaimRequest,
    idempotency_key: str = Depends(get_idempotency_key),
    _: str = Depends(get_authorization_header),
    __: str = Depends(get_request_id),
    ___: str = Depends(require_roles("service", "admin", "worker")),
    ____: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = ClaimService(db)
    claim = service.auto_create_claim(
        user_id=payload.user_id,
        event_id=payload.event_id,
        idempotency_key=idempotency_key,
    )
    return success_response({"claim_id": claim.id, "status": claim.status})


@router.get("/{user_id}", response_model=StandardResponse)
def get_claims_for_user(
    user_id: UUID,
    current_subject: UUID = Depends(get_current_subject),
    role: str = Depends(require_roles("worker", "service", "admin")),
    _: str = Depends(get_request_id),
    __: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    if role == "worker" and current_subject != user_id:
        raise AppError("Workers can access only their own claims.", "FORBIDDEN", 403)

    service = ClaimService(db)
    rows = service.list_claims_for_user(user_id)
    return success_response([row.model_dump() for row in rows])


@router.get("/detail/{claim_id}", response_model=StandardResponse)
def get_claim_detail(
    claim_id: UUID,
    current_subject: UUID = Depends(get_current_subject),
    role: str = Depends(require_roles("worker", "service", "admin")),
    _: str = Depends(get_request_id),
    __: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = ClaimService(db)
    detail = service.get_claim_detail(claim_id)

    if role == "worker" and current_subject != detail.user_id:
        raise AppError("Workers can access only their own claims.", "FORBIDDEN", 403)

    return success_response(detail.model_dump())


@router.post("/process", response_model=StandardResponse, status_code=status.HTTP_202_ACCEPTED)
def process_claim(
    payload: ProcessClaimRequest,
    token: str = Depends(get_authorization_header),
    request_id: str = Depends(get_request_id),
    _: str = Depends(require_roles("service", "admin")),
    __: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = ClaimService(db)
    result = service.process_claim(claim_id=payload.claim_id, token=token, request_id=request_id)
    return success_response(result.model_dump())
