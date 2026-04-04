from __future__ import annotations


def test_fraud_check_pass(client, auth_headers):
    response = client.post(
        "/api/v1/fraud/check",
        headers=auth_headers,
        json={
            "claim_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "activity": {
                "gps_valid": True,
                "activity_score": 0.95,
                "device_consistency": True,
            },
            "event": {
                "zone": "Chennai-South",
                "type": "weather",
                "severity": "MEDIUM",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["status"] == "PASS"


def test_fraud_check_fail(client, auth_headers):
    response = client.post(
        "/api/v1/fraud/check",
        headers=auth_headers,
        json={
            "claim_id": "22222222-2222-2222-2222-222222222222",
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "activity": {
                "gps_valid": False,
                "activity_score": 0.2,
                "device_consistency": False,
            },
            "event": {
                "zone": "Chennai-South",
                "type": "platform",
                "severity": "HIGH",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["status"] == "FAIL"
    assert body["data"]["fraud_score"] >= 0.7


def test_missing_request_id_rejected(client, auth_headers):
    headers = dict(auth_headers)
    headers.pop("X-Request-ID")

    response = client.post(
        "/api/v1/fraud/check",
        headers=headers,
        json={
            "claim_id": "33333333-3333-3333-3333-333333333333",
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "activity": {
                "gps_valid": True,
                "activity_score": 0.8,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_REQUEST_ID"


def test_get_fraud_log(client, auth_headers):
    claim_id = "44444444-4444-4444-4444-444444444444"
    create_response = client.post(
        "/api/v1/fraud/check",
        headers=auth_headers,
        json={
            "claim_id": claim_id,
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "activity": {
                "gps_valid": True,
                "activity_score": 0.9,
            },
        },
    )
    assert create_response.status_code == 200

    response = client.get(f"/api/v1/fraud/{claim_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["claim_id"] == claim_id
    assert "timestamp" in body["data"]


def test_get_fraud_log_not_found(client, auth_headers):
    response = client.get(
        "/api/v1/fraud/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FRAUD_LOG_NOT_FOUND"


def test_manual_override_requires_admin(client, auth_headers):
    response = client.post(
        "/api/v1/fraud/override",
        headers=auth_headers,
        json={
            "claim_id": "11111111-1111-1111-1111-111111111111",
            "override_status": "FAIL",
            "reason": "manual review",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_manual_override_success(client, auth_headers, admin_headers):
    claim_id = "55555555-5555-5555-5555-555555555555"
    create_response = client.post(
        "/api/v1/fraud/check",
        headers=auth_headers,
        json={
            "claim_id": claim_id,
            "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "activity": {
                "gps_valid": True,
                "activity_score": 0.95,
            },
        },
    )
    assert create_response.status_code == 200

    response = client.post(
        "/api/v1/fraud/override",
        headers=admin_headers,
        json={
            "claim_id": claim_id,
            "override_status": "FAIL",
            "reason": "manual fraud confirmation",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["status"] == "updated"
    assert body["data"]["override_status"] == "FAIL"
