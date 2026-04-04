from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.core.config import get_settings
from app.core.constants import COVERAGE_RATE_MAP, GST_PERCENT, ZONE_RATE_MAP
from app.core.exceptions import AppError
from app.schemas.policy import PremiumBreakdownData


TWOPLACES = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class PricingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def stabilization_factor(policy_week: int) -> Decimal:
        return Decimal("1.05") if policy_week <= 4 else Decimal("1.00")

    def calculate(
        self,
        *,
        weekly_income: Decimal,
        zone: str,
        policy_week: int = 1,
        risk_multiplier: Decimal = Decimal("1.00"),
    ) -> PremiumBreakdownData:
        if zone not in ZONE_RATE_MAP:
            raise AppError("Unsupported zone.", "INVALID_ZONE", 400)

        zone_rate = ZONE_RATE_MAP[zone]
        coverage_rate = COVERAGE_RATE_MAP[zone]
        stabilization_factor = self.stabilization_factor(policy_week)
        gst_rate = Decimal(str(self.settings.gst_rate)) if self.settings.gst_rate else GST_PERCENT

        base_premium = weekly_income * zone_rate * stabilization_factor * risk_multiplier
        base_premium = _money(base_premium)
        gst = _money(base_premium * gst_rate)
        total_premium = _money(base_premium + gst)

        return PremiumBreakdownData(
            weekly_income=_money(weekly_income),
            zone=zone,
            zone_rate=zone_rate,
            coverage_rate=coverage_rate,
            stabilization_factor=stabilization_factor,
            risk_multiplier=_money(risk_multiplier),
            base_premium=base_premium,
            gst=gst,
            total_premium=total_premium,
        )