from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DashboardData(BaseModel):
    active_users: int = 0
    active_sessions_last_hour: int = 0
    active_policies: int = 0
    total_claims: int = 0
    approved_claims: int = 0
    claims_rate: float = 0.0
    total_payout: float = 0.0
    payout_transactions: int = 0
    fraud_detected: int = 0
    service_event_volume: int = 0
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    top_impacted_zones: list[dict] = Field(default_factory=list)
    window_start: datetime
    window_end: datetime


class ZoneAnalyticsItem(BaseModel):
    zone: str
    risk_level: str
    claims: int = 0
    payout: float = 0.0
    disruptions: int = 0
    fraud_flags: int = 0
    active_users: int = 0


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: float


class TimeSeriesData(BaseModel):
    metric_type: str
    interval: str
    points: list[TimeSeriesPoint] = Field(default_factory=list)
