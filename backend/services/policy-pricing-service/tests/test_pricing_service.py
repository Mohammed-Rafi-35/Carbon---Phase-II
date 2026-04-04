from __future__ import annotations

from decimal import Decimal

from app.services.pricing_service import PricingService


def test_calculate_premium_mr2_week1():
    result = PricingService().calculate(
        weekly_income=Decimal("10000"),
        zone="MR-2",
        policy_week=1,
        risk_multiplier=Decimal("1.00"),
    )

    assert result.zone == "MR-2"
    assert result.base_premium == Decimal("262.50")
    assert result.gst == Decimal("47.25")
    assert result.total_premium == Decimal("309.75")
    assert result.coverage_rate == Decimal("0.70")


def test_stabilization_factor_after_week_4():
    result = PricingService().calculate(
        weekly_income=Decimal("10000"),
        zone="MR-2",
        policy_week=5,
        risk_multiplier=Decimal("1.00"),
    )

    assert result.stabilization_factor == Decimal("1.00")
    assert result.base_premium == Decimal("250.00")
