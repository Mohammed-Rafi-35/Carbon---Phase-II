from __future__ import annotations

from app.integrations.payment_gateway import PaymentResult


def test_process_payout_success(client, worker_headers):
    headers = dict(worker_headers)
    headers["Idempotency-Key"] = "idem-success-001"

    response = client.post(
        "/api/v1/payout/process",
        headers=headers,
        json={
            "claim_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30a1",
            "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
            "amount": 500,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["error"] is None
    assert body["data"]["transaction_id"]
    assert body["data"]["status"] == "completed"


def test_process_payout_idempotent_replay(client, worker_headers):
    headers = dict(worker_headers)
    headers["Idempotency-Key"] = "idem-replay-001"

    payload = {
        "claim_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30a2",
        "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
        "amount": 400,
    }

    first = client.post("/api/v1/payout/process", headers=headers, json=payload)
    second = client.post("/api/v1/payout/process", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["transaction_id"] == second.json()["data"]["transaction_id"]


def test_duplicate_claim_rejected(client, worker_headers):
    payload = {
        "claim_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30a3",
        "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
        "amount": 350,
    }

    first_headers = dict(worker_headers)
    first_headers["Idempotency-Key"] = "idem-dup-001"

    second_headers = dict(worker_headers)
    second_headers["Idempotency-Key"] = "idem-dup-002"

    first = client.post("/api/v1/payout/process", headers=first_headers, json=payload)
    second = client.post("/api/v1/payout/process", headers=second_headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_PAYOUT"


def test_missing_idempotency_key_rejected(client, worker_headers):
    headers = dict(worker_headers)
    headers.pop("Idempotency-Key", None)

    response = client.post(
        "/api/v1/payout/process",
        headers=headers,
        json={
            "claim_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30a4",
            "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
            "amount": 250,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"


def test_get_payout_history_success(client, worker_headers):
    headers = dict(worker_headers)
    headers["Idempotency-Key"] = "idem-history-001"

    client.post(
        "/api/v1/payout/process",
        headers=headers,
        json={
            "claim_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30a5",
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "amount": 150,
        },
    )

    history = client.get(
        "/api/v1/payout/16fd2706-8baf-433b-82eb-8c7fada847da",
        headers=worker_headers,
    )

    assert history.status_code == 200
    body = history.json()
    assert body["status"] == "success"
    assert len(body["data"]) == 1


def test_worker_cannot_get_other_user_history(client, worker_headers):
    response = client.get(
        "/api/v1/payout/8beea6d7-c470-45ff-b0a0-4e025fdb0f2f",
        headers=worker_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_retry_failed_payout_success(client, service_headers, monkeypatch):
    def fail_gateway(*args, **kwargs):
        _ = args
        _ = kwargs
        return PaymentResult(success=False, transaction_ref=None, reason="simulated")

    monkeypatch.setattr("app.services.payout_service.PaymentGatewayClient.process_payout", fail_gateway)

    process_headers = dict(service_headers)
    process_headers["Idempotency-Key"] = "idem-retry-001"

    failed = client.post(
        "/api/v1/payout/process",
        headers=process_headers,
        json={
            "claim_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30a6",
            "user_id": "8beea6d7-c470-45ff-b0a0-4e025fdb0f2f",
            "amount": 100,
        },
    )
    assert failed.status_code == 500

    history = client.get(
        "/api/v1/payout/8beea6d7-c470-45ff-b0a0-4e025fdb0f2f",
        headers=service_headers,
    )
    transaction_id = history.json()["data"][0]["transaction_id"]

    def succeed_gateway(*args, **kwargs):
        _ = args
        _ = kwargs
        return PaymentResult(success=True, transaction_ref="MOCK-RETRY-SUCCESS")

    monkeypatch.setattr("app.services.payout_service.PaymentGatewayClient.process_payout", succeed_gateway)

    retried = client.post(
        "/api/v1/payout/retry",
        headers=service_headers,
        json={"transaction_id": transaction_id},
    )

    assert retried.status_code == 200
    assert retried.json()["data"]["status"] == "retry_initiated"


def test_retry_transaction_not_found(client, service_headers):
    response = client.post(
        "/api/v1/payout/retry",
        headers=service_headers,
        json={"transaction_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TRANSACTION_NOT_FOUND"


def test_health_contract(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["service"] == "payout-service"
    assert payload["data"]["checks"]["database"] in {"up", "down"}
