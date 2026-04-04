from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import enforce_rate_limit, get_request_id, require_roles
from app.schemas.common import StandardResponse
from app.schemas.risk_schema import (
    FeedbackData,
    FeedbackRequest,
    PredictionLogData,
    RiskEvaluateData,
    RiskEvaluateRequest,
    RiskHealthData,
)
from app.services.inference_service import InferenceService
from app.utils.responses import success_response


router = APIRouter(prefix="/risk", tags=["risk"])
service = InferenceService()


@router.post("/evaluate", response_model=StandardResponse)
def evaluate_risk(
    payload: RiskEvaluateRequest,
    _: str = Depends(require_roles("worker", "service", "admin")),
    __: None = Depends(enforce_rate_limit),
    ___: str = Depends(get_request_id),
) -> dict:
    result: RiskEvaluateData = service.evaluate(payload)
    return success_response(result.model_dump())


@router.get("/health", response_model=StandardResponse)
def risk_health() -> dict:
    data = RiskHealthData(**service.health())
    return success_response(data.model_dump())


@router.post("/feedback", response_model=StandardResponse)
def submit_feedback(
    payload: FeedbackRequest,
    _: str = Depends(require_roles("service", "admin")),
    __: None = Depends(enforce_rate_limit),
) -> dict:
    updated = service.submit_feedback(payload)
    if not updated:
        return {
            "status": "error",
            "data": None,
            "error": {
                "code": "NOT_FOUND",
                "message": "Prediction log was not found.",
            },
        }

    data = FeedbackData(prediction_id=payload.prediction_id, review_status="reviewed")
    return success_response(data.model_dump())


@router.get("/feedback", response_model=StandardResponse)
def list_feedback(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    _: str = Depends(require_roles("service", "admin")),
) -> dict:
    rows = service.list_feedback(status=status, limit=limit)
    data = [PredictionLogData(**row).model_dump() for row in rows]
    return success_response(data)


@router.get("/drift", response_model=StandardResponse)
def drift_report(_: str = Depends(require_roles("service", "admin"))) -> dict:
    return success_response(service.drift_report())
