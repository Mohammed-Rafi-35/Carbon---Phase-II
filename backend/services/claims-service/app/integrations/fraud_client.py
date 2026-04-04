from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class FraudCheckResult:
    status: str
    fraud_score: float
    reason: str | None = None
    degraded: bool = False


class FraudServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.fraud_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def check_claim(
        self,
        *,
        claim_id: str,
        user_id: str,
        token: str,
        event_context: dict | None = None,
        request_id: str | None = None,
    ) -> FraudCheckResult:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        payload = {
            "claim_id": claim_id,
            "user_id": user_id,
            "activity": {
                "gps_valid": True,
                "activity_score": 0.8,
            },
        }
        if event_context:
            payload["event"] = event_context

        try:
            response = self.client.post("/api/v1/fraud/check", headers=headers, json=payload)
            if response.status_code >= 400:
                return FraudCheckResult(
                    status="PASS",
                    fraud_score=0.0,
                    reason="Fraud service unavailable",
                    degraded=response.status_code >= 500,
                )

            body = response.json()
            data = body.get("data", body)
            status = str(data.get("status", "PASS")).upper()
            fraud_score = float(data.get("fraud_score", 0.0))
            reason = data.get("reason")
            return FraudCheckResult(status=status, fraud_score=fraud_score, reason=reason)
        except Exception:
            return FraudCheckResult(
                status="PASS",
                fraud_score=0.0,
                reason="Fraud service unavailable",
                degraded=True,
            )
