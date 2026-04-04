from __future__ import annotations

from decimal import Decimal

import httpx

from app.integrations.ai_risk_client import AIRiskServiceClient
from app.integrations.claims_client import ClaimsServiceClient
from app.integrations.fraud_client import FraudServiceClient
from app.integrations.identity_client import IdentityServiceClient


def test_identity_client_get_worker_profile_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/workers/u1"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "user_id": "u1",
                    "zone": "MR-2",
                    "status": "active",
                },
                "error": None,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://identity")
    identity = IdentityServiceClient(client=client)
    result = identity.get_worker_profile("u1", token="token", request_id="req-1")
    assert result["data"]["zone"] == "MR-2"


def test_fraud_client_fail_response_means_flagged():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "success", "data": {"status": "FAIL"}})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fraud")
    fraud = FraudServiceClient(client=client)
    assert fraud.is_user_flagged("u1", "p1", token="token") is True


def test_ai_risk_multiplier_defaults_on_error():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"status": "error"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://risk")
    risk = AIRiskServiceClient(client=client)
    assert risk.get_premium_multiplier("MR-2", token="token") == Decimal("1.00")


def test_claims_client_get_claims_for_user_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/claims/u1"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": [
                    {
                        "claim_id": "c1",
                        "status": "approved",
                        "payout_amount": 500,
                    }
                ],
                "error": None,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://claims")
    claims = ClaimsServiceClient(client=client)
    result = claims.get_claims_for_user("u1", token="token", request_id="req-1")
    assert result["status"] == "success"
    assert result["data"][0]["claim_id"] == "c1"
