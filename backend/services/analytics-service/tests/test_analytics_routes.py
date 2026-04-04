from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.models.analytics_event import AnalyticsEvent
from app.services.ingestion_service import AnalyticsIngestionService


def _event(event_type: str, payload: dict, *, event_id: str, timestamp: datetime) -> dict:
    return {
        "event_type": event_type,
        "event_id": event_id,
        "timestamp": timestamp.isoformat(),
        "payload": payload,
    }


def test_dashboard_metrics_are_aggregated(client, db_session, admin_headers):
    service = AnalyticsIngestionService(db_session)
    now = datetime.now(tz=timezone.utc)

    service.process_event(_event("POLICY_CREATED", {"policy_id": "p1", "user_id": "u1", "zone": "MR-2", "total_premium": 120}, event_id="ev-1", timestamp=now))
    service.process_event(_event("CLAIM_INITIATED", {"claim_id": "c1", "user_id": "u1", "zone": "MR-2"}, event_id="ev-2", timestamp=now))
    service.process_event(_event("CLAIM_APPROVED", {"claim_id": "c1", "user_id": "u1", "amount": 500, "zone": "MR-2"}, event_id="ev-3", timestamp=now))
    service.process_event(_event("PAYOUT_COMPLETED", {"transaction_id": "t1", "claim_id": "c1", "user_id": "u1", "amount": 500, "zone": "MR-2"}, event_id="ev-4", timestamp=now))
    service.process_event(_event("FRAUD_DETECTED", {"claim_id": "c2", "user_id": "u2", "zone": "MR-2"}, event_id="ev-5", timestamp=now))
    service.process_event(_event("DISRUPTION_DETECTED", {"event_id": "d1", "zone": "MR-2", "severity": "HIGH"}, event_id="ev-6", timestamp=now))

    response = client.get("/api/v1/analytics/dashboard", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["active_policies"] == 1
    assert data["total_claims"] == 1
    assert data["approved_claims"] == 1
    assert data["payout_transactions"] == 1
    assert data["fraud_detected"] == 1
    assert float(data["total_payout"]) == 500.0
    assert data["risk_distribution"]["HIGH"] == 1


def test_zones_and_timeseries_endpoints(client, db_session, service_headers):
    service = AnalyticsIngestionService(db_session)
    now = datetime.now(tz=timezone.utc)

    service.process_event(_event("CLAIM_INITIATED", {"claim_id": "c10", "user_id": "u10", "zone": "Chennai-South"}, event_id="ev-10", timestamp=now))
    service.process_event(_event("PAYOUT_COMPLETED", {"transaction_id": "t10", "claim_id": "c10", "user_id": "u10", "amount": 450, "zone": "Chennai-South"}, event_id="ev-11", timestamp=now))
    service.process_event(_event("DISRUPTION_DETECTED", {"event_id": "d10", "zone": "Chennai-South", "severity": "MEDIUM"}, event_id="ev-12", timestamp=now))

    zones_response = client.get("/api/v1/analytics/zones?lookback_days=7", headers=service_headers)
    assert zones_response.status_code == 200
    zones = zones_response.json()["data"]
    assert any(item["zone"] == "Chennai-South" for item in zones)

    start = (now - timedelta(days=1)).isoformat()
    end = (now + timedelta(days=1)).isoformat()
    ts_response = client.get(
        "/api/v1/analytics/timeseries",
        params={
            "metric_type": "claims",
            "interval": "day",
            "start_date": start,
            "end_date": end,
        },
        headers=service_headers,
    )
    assert ts_response.status_code == 200
    points = ts_response.json()["data"]["points"]
    assert any(float(point["value"]) >= 1.0 for point in points)


def test_duplicate_event_is_ignored(db_session):
    service = AnalyticsIngestionService(db_session)
    now = datetime.now(tz=timezone.utc)
    payload = _event("CLAIM_INITIATED", {"claim_id": "dup-claim", "user_id": "u33", "zone": "MR-2"}, event_id="dup-1", timestamp=now)

    assert service.process_event(payload) is True
    assert service.process_event(payload) is False

    count_stmt = select(func.count()).select_from(AnalyticsEvent)
    count = int(db_session.execute(count_stmt).scalar_one())
    assert count == 1


def test_missing_request_id_is_rejected(client, admin_headers):
    headers = dict(admin_headers)
    headers.pop("X-Request-ID")

    response = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_REQUEST_ID"


def test_worker_role_cannot_access_admin_analytics(client, worker_headers):
    response = client.get("/api/v1/analytics/dashboard", headers=worker_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
