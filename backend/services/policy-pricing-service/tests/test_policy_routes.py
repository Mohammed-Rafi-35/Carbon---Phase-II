from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import OperationalError

from app.models.policy import Policy


def test_create_policy_success(client, worker_headers):
    response = client.post(
        "/api/v1/policy/create",
        headers=worker_headers,
        json={
            "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
            "weekly_income": 10500,
            "zone": "MR-2",
            "activity_days": 5,
            "policy_week": 1,
            "premium_paid": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["error"] is None
    assert body["data"]["policy_id"]
    assert body["data"]["total_premium"] == "325.24"


def test_get_policy_success(client, worker_headers):
    create = client.post(
        "/api/v1/policy/create",
        headers=worker_headers,
        json={
            "user_id": "9c031f3f-3639-45ac-8fe2-ef4f09ce84f6",
            "weekly_income": 10000,
            "zone": "LR-1",
            "activity_days": 4,
            "policy_week": 2,
            "premium_paid": True,
        },
    )
    assert create.status_code == 201

    response = client.get(
        "/api/v1/policy/9c031f3f-3639-45ac-8fe2-ef4f09ce84f6",
        headers=worker_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["zone"] == "LR-1"


def test_validate_policy_success_after_waiting_period(client, db_session, worker_headers, service_headers):
    create = client.post(
        "/api/v1/policy/create",
        headers=worker_headers,
        json={
            "user_id": "e20b8f5f-b32c-4a95-a06a-4f4de9da5fd2",
            "weekly_income": 9000,
            "zone": "MR-2",
            "activity_days": 6,
            "policy_week": 1,
            "premium_paid": True,
        },
    )
    policy_id = create.json()["data"]["policy_id"]

    policy = db_session.get(Policy, UUID(policy_id))
    policy.waiting_period_end = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    db_session.add(policy)
    db_session.commit()

    response = client.post(
        "/api/v1/policy/validate",
        headers=service_headers,
        json={
            "user_id": "e20b8f5f-b32c-4a95-a06a-4f4de9da5fd2",
            "policy_id": policy_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["valid"] is True


def test_validate_policy_waiting_period_not_completed(client, worker_headers, service_headers):
    create = client.post(
        "/api/v1/policy/create",
        headers=worker_headers,
        json={
            "user_id": "19895fef-f8e0-4f7f-b2ea-37d9be3f77a9",
            "weekly_income": 8500,
            "zone": "MR-2",
            "activity_days": 5,
            "policy_week": 1,
            "premium_paid": True,
        },
    )
    policy_id = create.json()["data"]["policy_id"]

    response = client.post(
        "/api/v1/policy/validate",
        headers=service_headers,
        json={
            "user_id": "19895fef-f8e0-4f7f-b2ea-37d9be3f77a9",
            "policy_id": policy_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["valid"] is False
    assert "Waiting period" in response.json()["data"]["reason"]


def test_validate_policy_rejects_insufficient_activity_days(client, db_session, worker_headers, service_headers):
    create = client.post(
        "/api/v1/policy/create",
        headers=worker_headers,
        json={
            "user_id": "4f9c8d8b-daf6-4f59-a176-4e2f1e8de111",
            "weekly_income": 9000,
            "zone": "LR-1",
            "activity_days": 2,
            "policy_week": 1,
            "premium_paid": True,
        },
    )
    policy_id = create.json()["data"]["policy_id"]

    policy = db_session.get(Policy, UUID(policy_id))
    policy.waiting_period_end = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    db_session.add(policy)
    db_session.commit()

    response = client.post(
        "/api/v1/policy/validate",
        headers=service_headers,
        json={
            "user_id": "4f9c8d8b-daf6-4f59-a176-4e2f1e8de111",
            "policy_id": policy_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["valid"] is False
    assert "Insufficient activity days" in response.json()["data"]["reason"]


def test_validate_policy_rejects_unpaid_premium(client, db_session, worker_headers, service_headers):
    create = client.post(
        "/api/v1/policy/create",
        headers=worker_headers,
        json={
            "user_id": "12f7be50-3fdf-40b4-b03e-5bd443f8fd90",
            "weekly_income": 9000,
            "zone": "MR-2",
            "activity_days": 5,
            "policy_week": 1,
            "premium_paid": False,
        },
    )
    policy_id = create.json()["data"]["policy_id"]

    policy = db_session.get(Policy, UUID(policy_id))
    policy.waiting_period_end = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    db_session.add(policy)
    db_session.commit()

    response = client.post(
        "/api/v1/policy/validate",
        headers=service_headers,
        json={
            "user_id": "12f7be50-3fdf-40b4-b03e-5bd443f8fd90",
            "policy_id": policy_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["valid"] is False
    assert response.json()["data"]["reason"] == "Premium is not paid"


def test_validate_policy_rejects_fraud_flag(client, db_session, worker_headers, service_headers, monkeypatch):
    monkeypatch.setattr("app.integrations.fraud_client.FraudServiceClient.is_user_flagged", lambda *args, **kwargs: True)

    create = client.post(
        "/api/v1/policy/create",
        headers=worker_headers,
        json={
            "user_id": "a52d2e0f-ea39-4a56-bdb4-4f5f3a4efa1c",
            "weekly_income": 9000,
            "zone": "MR-2",
            "activity_days": 6,
            "policy_week": 1,
            "premium_paid": True,
        },
    )
    policy_id = create.json()["data"]["policy_id"]

    policy = db_session.get(Policy, UUID(policy_id))
    policy.waiting_period_end = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    db_session.add(policy)
    db_session.commit()

    response = client.post(
        "/api/v1/policy/validate",
        headers=service_headers,
        json={
            "user_id": "a52d2e0f-ea39-4a56-bdb4-4f5f3a4efa1c",
            "policy_id": policy_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["valid"] is False
    assert response.json()["data"]["reason"] == "Fraud flag detected"


def test_calculate_pricing_requires_service_role(client, service_headers):
    response = client.post(
        "/api/v1/pricing/calculate",
        headers=service_headers,
        json={
            "weekly_income": 10000,
            "zone": "HR-3",
            "policy_week": 1,
            "risk_multiplier": 1.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["base_premium"] == "420.00"


def test_missing_request_id_rejected(client, worker_headers):
    bad_headers = dict(worker_headers)
    bad_headers.pop("X-Request-ID")

    response = client.post(
        "/api/v1/policy/create",
        headers=bad_headers,
        json={
            "user_id": "2005ed52-28f5-47dc-ae1c-bf0e2e69e209",
            "weekly_income": 11000,
            "zone": "MR-2",
            "activity_days": 5,
            "policy_week": 1,
            "premium_paid": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_REQUEST_ID"


def test_db_operational_error_returns_503(client, worker_headers, monkeypatch):
    def _raise_operational_error(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("db-down"))

    monkeypatch.setattr("app.services.policy_service.PolicyService.get_policy_by_user", _raise_operational_error)

    response = client.get(
        "/api/v1/policy/6a9ff576-6af6-4ef6-9f50-007ccf43f4d0",
        headers=worker_headers,
    )

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["data"] is None
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"
