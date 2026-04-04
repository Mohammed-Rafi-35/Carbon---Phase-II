from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.constants import IDEMPOTENCY_KEY_HEADER_NAME


@dataclass
class PayoutProcessResult:
    success: bool
    status: str | None = None
    transaction_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class PayoutServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.client = client or httpx.Client(
            base_url=settings.payout_service_url,
            timeout=settings.integration_timeout_seconds,
        )

    def process_payout(
        self,
        *,
        claim_id: str,
        user_id: str,
        amount: float,
        token: str,
        request_id: str,
        idempotency_key: str,
    ) -> PayoutProcessResult:
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Request-ID": request_id,
            IDEMPOTENCY_KEY_HEADER_NAME: idempotency_key,
        }
        payload = {
            "claim_id": claim_id,
            "user_id": user_id,
            "amount": amount,
        }

        try:
            response = self.client.post("/api/v1/payout/process", headers=headers, json=payload)
            body = response.json() if response.content else {}
            data = body.get("data", body)
            error = body.get("error") if isinstance(body, dict) else None

            if response.status_code >= 400:
                return PayoutProcessResult(
                    success=False,
                    status="failed",
                    error_code=(error or {}).get("code") if isinstance(error, dict) else "PAYOUT_REQUEST_FAILED",
                    error_message=(error or {}).get("message") if isinstance(error, dict) else "Payout service call failed.",
                )

            return PayoutProcessResult(
                success=True,
                status=str(data.get("status", "completed")),
                transaction_id=str(data.get("transaction_id")) if data.get("transaction_id") else None,
            )
        except Exception as exc:
            return PayoutProcessResult(
                success=False,
                status="failed",
                error_code="PAYOUT_REQUEST_FAILED",
                error_message=str(exc),
            )
