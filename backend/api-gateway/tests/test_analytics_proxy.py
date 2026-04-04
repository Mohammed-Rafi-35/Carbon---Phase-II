from __future__ import annotations

import httpx
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app


client = TestClient(app)


def _valid_token() -> str:
    return jwt.encode({"sub": "admin-123"}, "change-me-in-production", algorithm="HS256")


def test_analytics_proxy_requires_bearer_token() -> None:
    response = client.get("/api/v1/analytics/dashboard")

    assert response.status_code == 401
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "UNAUTHORIZED"


def test_analytics_proxy_forwards_headers_and_params(monkeypatch) -> None:
    captured: dict = {}

    async def mock_request(self, method, url, params=None, headers=None, content=None):
        captured["method"] = method
        captured["url"] = url
        captured["params"] = list(params or [])
        captured["headers"] = dict(headers or {})
        captured["content"] = content
        return httpx.Response(
            status_code=200,
            json={"status": "success", "data": {"proxied": True}, "error": None},
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    token = _valid_token()
    response = client.get(
        "/api/v1/analytics/timeseries?metric_type=claims&interval=day",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Request-ID": "req-gateway-1",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert captured["method"] == "GET"
    assert captured["url"] == "http://analytics-service:8000/api/v1/analytics/timeseries"
    assert ("metric_type", "claims") in captured["params"]
    assert ("interval", "day") in captured["params"]
    lowered_headers = {key.lower(): value for key, value in captured["headers"].items()}
    assert lowered_headers["authorization"] == f"Bearer {token}"
    assert lowered_headers["x-request-id"] == "req-gateway-1"


def test_analytics_proxy_returns_gateway_timeout_error(monkeypatch) -> None:
    async def mock_request(self, method, url, params=None, headers=None, content=None):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    response = client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {_valid_token()}", "X-Request-ID": "req-timeout"},
    )

    assert response.status_code == 504
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "UPSTREAM_TIMEOUT"
