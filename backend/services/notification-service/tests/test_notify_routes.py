from __future__ import annotations


def test_send_notification_success(client, auth_headers):
    response = client.post(
        "/api/v1/notify/send",
        headers=auth_headers,
        json={
            "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
            "channel": "IN_APP",
            "type": "CLAIM_UPDATE",
            "message": "Your claim is approved",
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "success"
    assert body["error"] is None
    assert body["data"]["status"] == "queued"
    assert body["data"]["notification_id"]


def test_get_notification_history(client, auth_headers):
    client.post(
        "/api/v1/notify/send",
        headers=auth_headers,
        json={
            "user_id": "9c031f3f-3639-45ac-8fe2-ef4f09ce84f6",
            "channel": "IN_APP",
            "type": "PAYOUT",
            "message": "Payout processed",
        },
    )

    response = client.get(
        "/api/v1/notify/9c031f3f-3639-45ac-8fe2-ef4f09ce84f6",
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert isinstance(payload["data"], list)
    assert len(payload["data"]) == 1


def test_retry_notification(client, auth_headers):
    sent = client.post(
        "/api/v1/notify/send",
        headers=auth_headers,
        json={
            "user_id": "e20b8f5f-b32c-4a95-a06a-4f4de9da5fd2",
            "channel": "IN_APP",
            "type": "POLICY",
            "message": "Policy is active",
        },
    )
    notification_id = sent.json()["data"]["notification_id"]

    response = client.post(
        "/api/v1/notify/retry",
        headers=auth_headers,
        json={"notification_id": notification_id},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "retry_scheduled"


def test_missing_request_id_rejected(client, auth_headers):
    bad_headers = dict(auth_headers)
    bad_headers.pop("X-Request-ID")

    response = client.post(
        "/api/v1/notify/send",
        headers=bad_headers,
        json={
            "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
            "channel": "IN_APP",
            "type": "CLAIM_UPDATE",
            "message": "Your claim is approved",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_REQUEST_ID"
