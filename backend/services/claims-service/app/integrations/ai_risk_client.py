from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class RiskEvaluationResult:
    risk_score: float
    risk_category: str
    premium_multiplier: float
    degraded: bool = False


class AIRiskServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.settings = settings
        self.client = client or httpx.Client(
            base_url=settings.ai_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def evaluate_claim(
        self,
        *,
        zone: str | None,
        severity: str | None,
        event_type: str | None,
        token: str,
        request_id: str | None = None,
    ) -> RiskEvaluationResult:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        payload = {
            "zone": (zone or self.settings.risk_default_zone).strip() or self.settings.risk_default_zone,
            "metrics": self._build_metrics(severity=severity, event_type=event_type),
        }

        try:
            response = self.client.post("/api/v1/risk/evaluate", headers=headers, json=payload)
            if response.status_code >= 400:
                return RiskEvaluationResult(
                    risk_score=0.5,
                    risk_category="MEDIUM",
                    premium_multiplier=1.0,
                    degraded=response.status_code >= 500,
                )

            body = response.json()
            data = body.get("data", body)
            return RiskEvaluationResult(
                risk_score=float(data.get("risk_score", 0.5)),
                risk_category=str(data.get("risk_category", "MEDIUM")),
                premium_multiplier=float(data.get("premium_multiplier", 1.0)),
            )
        except Exception:
            return RiskEvaluationResult(
                risk_score=0.5,
                risk_category="MEDIUM",
                premium_multiplier=1.0,
                degraded=True,
            )

    @staticmethod
    def _build_metrics(*, severity: str | None, event_type: str | None) -> dict[str, float]:
        severity_map = {
            "LOW": 0.2,
            "MEDIUM": 0.5,
            "HIGH": 0.8,
        }
        event_weight = {
            "weather": 0.75,
            "traffic": 0.65,
            "platform": 0.55,
        }
        sev = severity_map.get(str(severity or "MEDIUM").upper(), 0.5)
        evt = event_weight.get(str(event_type or "platform").lower(), 0.55)
        base = (sev + evt) / 2

        return {
            "disruption_freq": round(base, 4),
            "duration": round(base * 0.9, 4),
            "traffic": round(evt, 4),
            "order_drop": round(min(1.0, sev * 1.1), 4),
            "activity": round(max(0.0, 1.0 - sev * 0.4), 4),
            "claims": round(base * 0.6, 4),
        }
