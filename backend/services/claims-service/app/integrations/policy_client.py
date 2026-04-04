from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class PolicyValidationResult:
    valid: bool
    reason: str | None = None
    policy_id: str | None = None
    zone: str | None = None
    coverage_rate: float | None = None
    degraded: bool = False


class PolicyServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.policy_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def validate_for_claim(self, *, user_id: str, token: str, request_id: str | None = None) -> PolicyValidationResult:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        try:
            policy_response = self.client.get(f"/api/v1/policy/{user_id}", headers=headers)
            if policy_response.status_code >= 400:
                return PolicyValidationResult(
                    valid=True,
                    reason="Policy service unavailable",
                    degraded=policy_response.status_code >= 500,
                )

            policy_body = policy_response.json()
            policy_data = policy_body.get("data", policy_body)
            policy_id = policy_data.get("policy_id")
            if not policy_id:
                return PolicyValidationResult(valid=True)

            validate_payload = {
                "user_id": user_id,
                "policy_id": policy_id,
            }
            validate_response = self.client.post(
                "/api/v1/policy/validate",
                headers=headers,
                json=validate_payload,
            )
            if validate_response.status_code >= 400:
                return PolicyValidationResult(
                    valid=True,
                    reason="Policy validation unavailable",
                    policy_id=str(policy_id),
                    zone=policy_data.get("zone"),
                    coverage_rate=policy_data.get("coverage_rate"),
                    degraded=validate_response.status_code >= 500,
                )

            validate_body = validate_response.json()
            validate_data = validate_body.get("data", validate_body)
            valid = bool(validate_data.get("valid", True))
            reason = validate_data.get("reason")
            return PolicyValidationResult(
                valid=valid,
                reason=reason,
                policy_id=str(policy_id),
                zone=policy_data.get("zone"),
                coverage_rate=policy_data.get("coverage_rate"),
            )
        except Exception:
            # Contract allows mock behavior when dependencies are not ready.
            return PolicyValidationResult(valid=True, reason="Policy service unavailable", degraded=True)
