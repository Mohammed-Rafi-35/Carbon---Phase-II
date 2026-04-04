from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.core.config import get_settings


@dataclass
class PaymentResult:
    success: bool
    transaction_ref: str | None
    reason: str | None = None


class PaymentGatewayClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def process_payout(self, *, payout_id: UUID, user_id: UUID, amount: Decimal) -> PaymentResult:
        _ = user_id

        if self.settings.mock_gateway_force_failure:
            return PaymentResult(success=False, transaction_ref=None, reason="Mock gateway forced failure")

        provider = self.settings.payment_provider.lower()
        transaction_ref = f"{provider.upper()}-{uuid.uuid4()}-{payout_id}"
        return PaymentResult(success=True, transaction_ref=transaction_ref)
