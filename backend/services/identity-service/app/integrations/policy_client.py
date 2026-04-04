from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppError


class PolicyServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.policy_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def validate_policy(self, user_id: str, policy_id: str, token: str, request_id: str | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        response = self.client.post(
            "/api/v1/policy/validate",
            json={"user_id": user_id, "policy_id": policy_id},
            headers=headers,
        )
        if response.status_code >= 400:
            raise AppError("Policy service unavailable.", "POLICY_INTEGRATION_ERROR", 502)
        return response.json()
