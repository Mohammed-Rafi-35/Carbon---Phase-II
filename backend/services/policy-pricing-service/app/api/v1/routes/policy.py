from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    enforce_rate_limit,
    get_authorization_header,
    get_db_session,
    get_request_id,
    require_roles,
)
from app.schemas.common import StandardResponse
from app.schemas.policy import CreatePolicyRequest, ValidatePolicyRequest
from app.services.policy_service import PolicyService
from app.utils.responses import success_response


router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/create", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: CreatePolicyRequest,
    token: str = Depends(get_authorization_header),
    request_id: str = Depends(get_request_id),
    _: str = Depends(require_roles("worker", "admin", "service")),
    __: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = PolicyService(db)
    policy = service.create_policy(payload, token=token, request_id=request_id)
    return success_response(policy.model_dump())


@router.get("/{user_id}", response_model=StandardResponse)
def get_active_policy(
    user_id: UUID,
    _: str = Depends(require_roles("worker", "admin", "service")),
    __: None = Depends(enforce_rate_limit),
    ___: str = Depends(get_request_id),
    db: Session = Depends(get_db_session),
) -> dict:
    service = PolicyService(db)
    policy = service.get_policy_by_user(user_id)
    return success_response(policy.model_dump())


@router.post("/validate", response_model=StandardResponse)
def validate_policy(
    payload: ValidatePolicyRequest,
    token: str = Depends(get_authorization_header),
    request_id: str = Depends(get_request_id),
    _: str = Depends(require_roles("service", "admin", "worker")),
    __: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    service = PolicyService(db)
    result = service.validate_policy(
        user_id=payload.user_id,
        policy_id=payload.policy_id,
        token=token,
        request_id=request_id,
    )
    return success_response(result.model_dump())