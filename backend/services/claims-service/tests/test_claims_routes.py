from __future__ import annotations

from app.integrations.ai_risk_client import RiskEvaluationResult
from app.integrations.fraud_client import FraudCheckResult
from app.integrations.payout_client import PayoutProcessResult
from app.integrations.policy_client import PolicyValidationResult


def test_auto_create_claim_success(client, service_headers):
    response = client.post(
        "/api/v1/claims/auto",
        headers=service_headers,
        json={
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "event_id": "11111111-1111-1111-1111-111111111111",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["status"] == "initiated"
    assert body["data"]["claim_id"]


def test_get_claims_for_worker_success(client, service_headers, worker_headers):
    client.post(
        "/api/v1/claims/auto",
        headers=service_headers,
        json={
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "event_id": "22222222-2222-2222-2222-222222222222",
        },
    )

    response = client.get(
        "/api/v1/claims/16fd2706-8baf-433b-82eb-8c7fada847da",
        headers=worker_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["data"]) == 1


def test_get_claim_detail_for_worker_success(client, service_headers, worker_headers):
    created = client.post(
        "/api/v1/claims/auto",
        headers=service_headers,
        json={
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "event_id": "77777777-7777-7777-7777-777777777777",
        },
    )
    claim_id = created.json()["data"]["claim_id"]

    response = client.get(
        f"/api/v1/claims/detail/{claim_id}",
        headers=worker_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["claim_id"] == claim_id
    assert data["status"] == "initiated"
    assert len(data["logs"]) >= 1


def test_process_claim_approved_and_paid(client, service_headers, monkeypatch):
    monkeypatch.setattr(
        "app.integrations.policy_client.PolicyServiceClient.validate_for_claim",
        lambda *args, **kwargs: PolicyValidationResult(
            valid=True,
            policy_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            zone="MR-2",
            coverage_rate=0.7,
        ),
    )
    monkeypatch.setattr(
        "app.integrations.ai_risk_client.AIRiskServiceClient.evaluate_claim",
        lambda *args, **kwargs: RiskEvaluationResult(
            risk_score=0.42,
            risk_category="MEDIUM",
            premium_multiplier=1.0,
        ),
    )
    monkeypatch.setattr(
        "app.integrations.fraud_client.FraudServiceClient.check_claim",
        lambda *args, **kwargs: FraudCheckResult(status="PASS", fraud_score=0.1, reason=None),
    )
    monkeypatch.setattr(
        "app.integrations.payout_client.PayoutServiceClient.process_payout",
        lambda *args, **kwargs: PayoutProcessResult(
            success=True,
            status="completed",
            transaction_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        ),
    )

    created = client.post(
        "/api/v1/claims/auto",
        headers=service_headers,
        json={
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "event_id": "33333333-3333-3333-3333-333333333333",
        },
    )
    claim_id = created.json()["data"]["claim_id"]

    processed = client.post(
        "/api/v1/claims/process",
        headers=service_headers,
        json={"claim_id": claim_id},
    )

    assert processed.status_code == 200
    data = processed.json()["data"]
    assert data["status"] == "approved"
    assert float(data["payout_amount"]) == 500.0

    detail = client.get(f"/api/v1/claims/detail/{claim_id}", headers=service_headers)
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["status"] == "paid"

    stages = [item["stage"] for item in detail_data["logs"]]
    assert stages[0] == "initiated"
    assert "validated" in stages
    assert "evaluated" in stages
    assert "approved" in stages
    assert "paid" in stages


def test_process_claim_rejected_by_fraud(client, service_headers, monkeypatch):
    monkeypatch.setattr(
        "app.integrations.policy_client.PolicyServiceClient.validate_for_claim",
        lambda *args, **kwargs: PolicyValidationResult(
            valid=True,
            policy_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            zone="MR-2",
            coverage_rate=0.7,
        ),
    )
    monkeypatch.setattr(
        "app.integrations.ai_risk_client.AIRiskServiceClient.evaluate_claim",
        lambda *args, **kwargs: RiskEvaluationResult(
            risk_score=0.5,
            risk_category="MEDIUM",
            premium_multiplier=1.0,
        ),
    )
    monkeypatch.setattr(
        "app.integrations.fraud_client.FraudServiceClient.check_claim",
        lambda *args, **kwargs: FraudCheckResult(status="FAIL", fraud_score=0.93, reason="Suspicious behavior"),
    )

    created = client.post(
        "/api/v1/claims/auto",
        headers=service_headers,
        json={
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "event_id": "44444444-4444-4444-4444-444444444444",
        },
    )
    claim_id = created.json()["data"]["claim_id"]

    processed = client.post(
        "/api/v1/claims/process",
        headers=service_headers,
        json={"claim_id": claim_id},
    )

    assert processed.status_code == 200
    data = processed.json()["data"]
    assert data["status"] == "rejected"
    assert data["payout_amount"] is None


def test_process_claim_rejected_by_policy(client, service_headers, monkeypatch):
    monkeypatch.setattr(
        "app.integrations.policy_client.PolicyServiceClient.validate_for_claim",
        lambda *args, **kwargs: PolicyValidationResult(valid=False, reason="Policy inactive"),
    )

    created = client.post(
        "/api/v1/claims/auto",
        headers=service_headers,
        json={
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "event_id": "66666666-6666-6666-6666-666666666666",
        },
    )
    claim_id = created.json()["data"]["claim_id"]

    processed = client.post(
        "/api/v1/claims/process",
        headers=service_headers,
        json={"claim_id": claim_id},
    )

    assert processed.status_code == 200
    data = processed.json()["data"]
    assert data["status"] == "rejected"
    assert data["payout_amount"] is None


def test_worker_cannot_access_other_user_claim_detail(client, service_headers, worker_headers):
    created = client.post(
        "/api/v1/claims/auto",
        headers=service_headers,
        json={
            "user_id": "12345678-1234-1234-1234-123456789abc",
            "event_id": "88888888-8888-8888-8888-888888888888",
        },
    )
    claim_id = created.json()["data"]["claim_id"]

    response = client.get(
        f"/api/v1/claims/detail/{claim_id}",
        headers=worker_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_missing_request_id_rejected(client, service_headers):
    headers = dict(service_headers)
    headers.pop("X-Request-ID")

    response = client.post(
        "/api/v1/claims/auto",
        headers=headers,
        json={
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "event_id": "55555555-5555-5555-5555-555555555555",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_REQUEST_ID"
