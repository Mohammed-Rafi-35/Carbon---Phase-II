from __future__ import annotations

from decimal import Decimal

import httpx

from app.core.config import get_settings


class AIRiskServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.ai_risk_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def get_premium_multiplier(self, zone: str, token: str, request_id: str | None = None) -> Decimal:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        payload = {
            "zone": zone,
            "metrics": {
                "disruption_freq": 0.4,
                "duration": 0.4,
                "traffic": 0.4,
                "order_drop": 0.4,
                "activity": 0.6,
                "claims": 0.3,
            },
        }
        try:
            response = self.client.post("/api/v1/risk/evaluate", json=payload, headers=headers)
            if response.status_code >= 400:
                return Decimal("1.00")
            body = response.json()
            data = body.get("data", body)
            raw_multiplier = data.get("premium_multiplier", 1.0)
            return Decimal(str(raw_multiplier))
        except Exception:
            return Decimal("1.00")