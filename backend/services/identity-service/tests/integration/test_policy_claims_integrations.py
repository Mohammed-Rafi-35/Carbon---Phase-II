from __future__ import annotations

import httpx
import pytest

from app.core.exceptions import AppError
from app.integrations.claims_client import ClaimsServiceClient
from app.integrations.policy_client import PolicyServiceClient


def test_policy_client_validate_policy_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/policy/validate"
        return httpx.Response(200, json={"status": "success", "data": {"valid": True}, "error": None})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://policy-service")
    policy_client = PolicyServiceClient(client=client)

    response = policy_client.validate_policy("u1", "p1", "token", "req-1")
    assert response["status"] == "success"
    assert response["data"]["valid"] is True


def test_claims_client_failure_raises_app_error():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"status": "error"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://claims-service")
    claims_client = ClaimsServiceClient(client=client)

    with pytest.raises(AppError) as exc:
        claims_client.get_claims_for_user("u1", "token")

    assert exc.value.error_code == "CLAIMS_INTEGRATION_ERROR"
