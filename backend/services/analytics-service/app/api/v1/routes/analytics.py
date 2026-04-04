from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    enforce_rate_limit,
    get_authorization_header,
    get_db_session,
    get_request_id,
    require_roles,
)
from app.schemas.common import StandardResponse
from app.services.analytics_service import AnalyticsService
from app.utils.responses import success_response


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=StandardResponse)
def get_dashboard_metrics(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    _: str = Depends(get_authorization_header),
    __: str = Depends(get_request_id),
    ___: str = Depends(require_roles("admin", "service")),
    ____: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    data = AnalyticsService(db).get_dashboard(start_date=start_date, end_date=end_date)
    return success_response(data)


@router.get("/zones", response_model=StandardResponse)
def get_zone_analytics(
    lookback_days: int = Query(default=30, ge=1, le=365),
    _: str = Depends(get_authorization_header),
    __: str = Depends(get_request_id),
    ___: str = Depends(require_roles("admin", "service")),
    ____: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    data = AnalyticsService(db).get_zone_analytics(lookback_days=lookback_days)
    return success_response(data)


@router.get("/timeseries", response_model=StandardResponse)
def get_timeseries_analytics(
    metric_type: str = Query(default="claims"),
    interval: str = Query(default="day"),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    _: str = Depends(get_authorization_header),
    __: str = Depends(get_request_id),
    ___: str = Depends(require_roles("admin", "service")),
    ____: None = Depends(enforce_rate_limit),
    db: Session = Depends(get_db_session),
) -> dict:
    data = AnalyticsService(db).get_timeseries(
        metric_type=metric_type,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )
    return success_response(data)


@router.get("/health", response_model=StandardResponse)
def analytics_health(
    _: str = Depends(get_authorization_header),
    __: str = Depends(get_request_id),
    ___: str = Depends(require_roles("admin", "service")),
    db: Session = Depends(get_db_session),
) -> dict:
    data = AnalyticsService(db).get_admin_health()
    return success_response(data)
