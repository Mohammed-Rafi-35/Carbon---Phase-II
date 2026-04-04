from __future__ import annotations

import httpx
from fastapi.testclient import TestClient
from jose import jwt

from app.config.settings import get_settings
from app.main import app
import app.routes.proxy_common as proxy_common


client = TestClient(app)


def _valid_token() -> str:
    return jwt.encode({"sub": "service-user"}, "change-me-in-production", algorithm="HS256")


def test_claims_proxy_forwards_to_claims_service(monkeypatch) -> None:
    captured: dict = {}

    async def mock_request(self, method, url, params=None, headers=None, content=None):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = dict(headers or {})
        return httpx.Response(
            status_code=202,
            json={"status": "success", "data": {"proxied": True}, "error": None},
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    response = client.post(
        "/api/v1/claims/process",
        json={"claim_id": "123"},
        headers={"Authorization": f"Bearer {_valid_token()}", "X-Request-ID": "req-claims-1"},
    )

    assert response.status_code == 202
    assert captured["method"] == "POST"
    assert captured["url"] == "http://claims-service:8000/api/v1/claims/process"
    lowered_headers = {key.lower(): value for key, value in captured["headers"].items()}
    assert lowered_headers["x-request-id"] == "req-claims-1"


def test_policy_proxy_routes_pricing_to_policy_service(monkeypatch) -> None:
    captured: dict = {}

    async def mock_request(self, method, url, params=None, headers=None, content=None):
        captured["url"] = url
        return httpx.Response(
            status_code=200,
            json={"status": "success", "data": {"premium": 100}, "error": None},
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    response = client.post(
        "/api/v1/pricing/calculate",
        json={"weekly_income": 10000, "zone": "MR-2"},
        headers={"Authorization": f"Bearer {_valid_token()}"},
    )

    assert response.status_code == 200
    assert captured["url"] == "http://policy-pricing-service:8000/api/v1/pricing/calculate"


def test_notification_proxy_routes_notify_to_notification_service(monkeypatch) -> None:
    captured: dict = {}

    async def mock_request(self, method, url, params=None, headers=None, content=None):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = dict(headers or {})
        return httpx.Response(
            status_code=202,
            json={"status": "success", "data": {"queued": True}, "error": None},
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    response = client.post(
        "/api/v1/notify/send",
        json={"type": "sms", "message": "hello", "user_ids": ["16fd2706-8baf-433b-82eb-8c7fada847da"]},
        headers={"Authorization": f"Bearer {_valid_token()}", "X-Request-ID": "req-notify-1"},
    )

    assert response.status_code == 202
    assert captured["method"] == "POST"
    assert captured["url"] == "http://notification-service:8000/api/v1/notify/send"
    lowered_headers = {key.lower(): value for key, value in captured["headers"].items()}
    assert lowered_headers["x-request-id"] == "req-notify-1"


def test_trigger_proxy_routes_trigger_to_trigger_service(monkeypatch) -> None:
    captured: dict = {}

    async def mock_request(self, method, url, params=None, headers=None, content=None):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = dict(headers or {})
        return httpx.Response(
            status_code=200,
            json={"status": "success", "data": [], "error": None},
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    response = client.get(
        "/api/v1/trigger/active",
        headers={"Authorization": f"Bearer {_valid_token()}", "X-Request-ID": "req-trigger-1"},
    )

    assert response.status_code == 200
    assert captured["method"] == "GET"
    assert captured["url"] == "http://trigger-service:8000/api/v1/trigger/active"
    lowered_headers = {key.lower(): value for key, value in captured["headers"].items()}
    assert lowered_headers["x-request-id"] == "req-trigger-1"


def test_invalid_jwt_is_rejected() -> None:
    response = client.get("/api/v1/claims/123", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "UNAUTHORIZED"


def test_request_body_larger_than_limit_is_rejected() -> None:
    huge_body = "x" * (1_048_576 + 1)

    response = client.post(
        "/api/v1/claims/process",
        json={"payload": huge_body},
        headers={"Authorization": f"Bearer {_valid_token()}"},
    )

    assert response.status_code == 413
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "REQUEST_TOO_LARGE"


def test_gateway_circuit_breaker_short_circuits_after_failures(monkeypatch) -> None:
    settings = get_settings()
    original_threshold = settings.circuit_breaker_failure_threshold
    original_open_seconds = settings.circuit_breaker_open_seconds
    try:
        settings.circuit_breaker_failure_threshold = 1
        settings.circuit_breaker_open_seconds = 60.0
        proxy_common.CIRCUIT_STATE.clear()

        call_count = {"value": 0}

        async def fail_request(self, method, url, params=None, headers=None, content=None):
            call_count["value"] += 1
            raise httpx.HTTPError("boom")

        monkeypatch.setattr(httpx.AsyncClient, "request", fail_request)

        first = client.get(
            "/api/v1/analytics/dashboard",
            headers={"Authorization": f"Bearer {_valid_token()}", "X-Request-ID": "req-cb-1"},
        )

        assert first.status_code == 502
        assert first.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"
        assert call_count["value"] >= 1

        before_second = call_count["value"]
        second = client.get(
            "/api/v1/analytics/dashboard",
            headers={"Authorization": f"Bearer {_valid_token()}", "X-Request-ID": "req-cb-2"},
        )

        assert second.status_code == 503
        assert second.json()["error"]["code"] == "CIRCUIT_OPEN"
        assert call_count["value"] == before_second
    finally:
        settings.circuit_breaker_failure_threshold = original_threshold
        settings.circuit_breaker_open_seconds = original_open_seconds
        proxy_common.CIRCUIT_STATE.clear()
