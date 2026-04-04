from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RiskMetrics(BaseModel):
    disruption_freq: float = Field(ge=0.0)
    duration: float = Field(ge=0.0)
    traffic: float = Field(ge=0.0)
    order_drop: float = Field(ge=0.0)
    activity: float = Field(ge=0.0)
    claims: float = Field(ge=0.0)

    @field_validator("*", mode="after")
    @classmethod
    def validate_finite(cls, value: float) -> float:
        if value != value:  # NaN check
            raise ValueError("Metric values must be finite numbers")
        return value


class RiskEvaluateRequest(BaseModel):
    zone: str = Field(min_length=1, max_length=50)
    metrics: RiskMetrics
    context: "RiskTemporalContext | None" = None

    @field_validator("zone")
    @classmethod
    def normalize_zone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("zone is required")
        return normalized


class RiskEvaluateData(BaseModel):
    risk_score: float
    risk_category: str
    premium_multiplier: float
    confidence: float
    top_factors: list[str]
    prediction_id: int | None = None
    model_version: str


class RiskHealthData(BaseModel):
    status: str
    model_version: str
    model_loaded: bool
    classification_strategy: str
    drift_status: str | None = None


class RiskTemporalContext(BaseModel):
    rolling_disruption_3h: float | None = Field(default=None, ge=0.0)
    traffic_last_hour: float | None = Field(default=None, ge=0.0)
    previous_risk_score: float | None = Field(default=None, ge=0.0)


class FeedbackRequest(BaseModel):
    prediction_id: int = Field(ge=1)
    actual_outcome: float | None = Field(default=None, ge=0.0, le=1.0)
    corrected_label: str | None = Field(default=None)
    review_notes: str | None = Field(default=None, max_length=500)

    @field_validator("corrected_label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError("corrected_label must be LOW, MEDIUM, or HIGH")
        return normalized


class FeedbackData(BaseModel):
    prediction_id: int
    review_status: str


class PredictionLogData(BaseModel):
    id: int
    created_at: str
    zone: str
    risk_score: float
    risk_category: str
    confidence: float
    model_version: str
    review_status: str
