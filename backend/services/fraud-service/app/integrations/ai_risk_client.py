from __future__ import annotations

import httpx

from app.core.config import get_settings


class AIRiskServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.ai_risk_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def evaluate_risk(
        self,
        *,
        zone: str,
        metrics: dict[str, float],
        token: str,
        request_id: str | None = None,
    ) -> float | None:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        payload = {
            "zone": zone,
            "metrics": metrics,
        }

        try:
            response = self.client.post("/api/v1/risk/evaluate", headers=headers, json=payload)
            if response.status_code >= 400:
                return None

            body = response.json()
            data = body.get("data", body)
            return float(data.get("risk_score"))
        except Exception:
            return None
