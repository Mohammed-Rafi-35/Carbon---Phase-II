from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import enforce_rate_limit, get_request_id, require_roles
from app.schemas.common import StandardResponse
from app.schemas.policy import CalculatePremiumRequest
from app.services.pricing_service import PricingService
from app.utils.responses import success_response


router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/calculate", response_model=StandardResponse)
def calculate_premium(
    payload: CalculatePremiumRequest,
    _: str = Depends(require_roles("service", "admin")),
    __: None = Depends(enforce_rate_limit),
    ___: str = Depends(get_request_id),
) -> dict:
    premium = PricingService().calculate(
        weekly_income=payload.weekly_income,
        zone=payload.zone,
        policy_week=payload.policy_week,
        risk_multiplier=payload.risk_multiplier,
    )
    return success_response(premium.model_dump())