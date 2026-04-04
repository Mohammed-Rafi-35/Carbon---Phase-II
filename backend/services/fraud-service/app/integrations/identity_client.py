from __future__ import annotations

import httpx

from app.core.config import get_settings


class IdentityServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.identity_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def get_worker_profile(
        self,
        *,
        user_id: str,
        token: str,
        request_id: str | None = None,
    ) -> dict | None:
        headers = {"Authorization": f"Bearer {token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        try:
            response = self.client.get(f"/api/v1/workers/{user_id}", headers=headers)
            if response.status_code >= 400:
                return None

            body = response.json()
            data = body.get("data", body)
            if isinstance(data, dict):
                return data
            return None
        except Exception:
            return None
