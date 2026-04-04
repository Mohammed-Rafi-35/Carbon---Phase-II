from __future__ import annotations

import httpx
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app


client = TestClient(app)


def _valid_token() -> str:
    return jwt.encode({"sub": "worker-123"}, "change-me-in-production", algorithm="HS256")


def test_identity_auth_proxy_forwards_post_body_and_headers(monkeypatch) -> None:
    captured: dict = {}

    async def mock_request(self, method, url, params=None, headers=None, content=None):
        captured["method"] = method
        captured["url"] = url
        captured["params"] = list(params or [])
        captured["headers"] = dict(headers or {})
        captured["content"] = content
        return httpx.Response(
            status_code=201,
            json={"status": "success", "data": {"registered": True}, "error": None},
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    response = client.post(
        "/api/v1/auth/register?source=frontend",
        json={"email": "worker@example.com", "password": "Passw0rd!"},
        headers={"X-Request-ID": "req-identity-1"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert captured["method"] == "POST"
    assert captured["url"] == "http://identity-service:8000/api/v1/auth/register"
    assert ("source", "frontend") in captured["params"]
    lowered_headers = {key.lower(): value for key, value in captured["headers"].items()}
    assert lowered_headers["x-request-id"] == "req-identity-1"
    assert lowered_headers["content-type"].startswith("application/json")
    assert b"worker@example.com" in captured["content"]


def test_identity_workers_proxy_forwards_auth_header(monkeypatch) -> None:
    captured: dict = {}

    async def mock_request(self, method, url, params=None, headers=None, content=None):
        captured["url"] = url
        captured["headers"] = dict(headers or {})
        return httpx.Response(
            status_code=200,
            json={"status": "success", "data": {"id": "w-1"}, "error": None},
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    token = _valid_token()
    response = client.get(
        "/api/v1/workers/worker-123",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Request-ID": "req-workers-1",
        },
    )

    assert response.status_code == 200
    assert captured["url"] == "http://identity-service:8000/api/v1/workers/worker-123"
    lowered_headers = {key.lower(): value for key, value in captured["headers"].items()}
    assert lowered_headers["authorization"] == f"Bearer {token}"
    assert lowered_headers["x-request-id"] == "req-workers-1"


def test_identity_proxy_returns_gateway_timeout_error(monkeypatch) -> None:
    async def mock_request(self, method, url, params=None, headers=None, content=None):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "worker@example.com", "password": "Passw0rd!"},
        headers={"X-Request-ID": "req-timeout-identity"},
    )

    assert response.status_code == 504
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "UPSTREAM_TIMEOUT"
