from __future__ import annotations

import httpx

from app.core.config import get_settings


class FraudServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.fraud_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def is_user_flagged(self, user_id: str, policy_id: str, token: str, request_id: str | None = None) -> bool:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        payload = {
            "claim_id": policy_id,
            "user_id": user_id,
            "activity": {
                "gps_valid": True,
                "activity_score": 1.0,
            },
        }
        try:
            response = self.client.post("/api/v1/fraud/check", headers=headers, json=payload)
        except Exception:
            return False
        if response.status_code >= 400:
            return False
        body = response.json()
        status = str(body.get("data", {}).get("status") or body.get("status") or "PASS").upper()
        return status == "FAIL"