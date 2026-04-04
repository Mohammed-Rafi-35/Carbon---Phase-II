from __future__ import annotations

from app.core.config import get_settings


def test_trigger_lifecycle(client, auth_headers):
    payload = {
        "zone": "MR-2",
        "type": "weather",
        "severity": "HIGH",
    }

    create_response = client.post("/api/v1/trigger/mock", json=payload, headers=auth_headers)
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["status"] == "success"
    assert body["error"] is None
    assert body["data"]["status"] == "triggered"
    event_id = body["data"]["event_id"]

    active_response = client.get("/api/v1/trigger/active", headers=auth_headers)
    assert active_response.status_code == 200
    active_body = active_response.json()
    assert active_body["status"] == "success"
    assert len(active_body["data"]) == 1
    assert active_body["data"][0]["event_id"] == event_id

    stop_response = client.post("/api/v1/trigger/stop", json={"event_id": event_id}, headers=auth_headers)
    assert stop_response.status_code == 200
    stop_body = stop_response.json()
    assert stop_body["status"] == "success"
    assert stop_body["data"]["status"] == "stopped"

    active_after_stop = client.get("/api/v1/trigger/active", headers=auth_headers)
    assert active_after_stop.status_code == 200
    assert active_after_stop.json()["data"] == []


def test_requires_request_id(client, auth_headers):
    headers = {"Authorization": auth_headers["Authorization"]}
    response = client.get("/api/v1/trigger/active", headers=headers)
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "MISSING_REQUEST_ID"


def test_stop_nonexistent_event(client, auth_headers):
    response = client.post(
        "/api/v1/trigger/stop",
        json={"event_id": "8a3baec8-e521-438f-a8a2-d6ed2f2f8f15"},
        headers=auth_headers,
    )
    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "EVENT_NOT_FOUND"


def test_manual_trigger_disabled(client, auth_headers):
    settings = get_settings()
    previous = settings.enable_manual_trigger
    settings.enable_manual_trigger = False
    try:
        response = client.post(
            "/api/v1/trigger/mock",
            json={"zone": "MR-2", "type": "weather", "severity": "HIGH"},
            headers=auth_headers,
        )
    finally:
        settings.enable_manual_trigger = previous

    assert response.status_code == 403
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "MANUAL_TRIGGER_DISABLED"


def test_health_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["service"] == "trigger-service"
    assert payload["data"]["checks"]["database"] in {"up", "down"}
