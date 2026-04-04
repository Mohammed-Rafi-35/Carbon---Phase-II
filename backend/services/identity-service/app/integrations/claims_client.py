from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppError


class ClaimsServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.claims_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def get_claims_for_user(self, user_id: str, token: str, request_id: str | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        response = self.client.get(f"/api/v1/claims/{user_id}", headers=headers)
        if response.status_code >= 400:
            raise AppError("Claims service unavailable.", "CLAIMS_INTEGRATION_ERROR", 502)
        return response.json()
