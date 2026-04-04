from __future__ import annotations


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def normalize_metric(value: float | int | None) -> float:
    if value is None:
        return 0.5

    numeric = float(value)
    if numeric > 1.0:
        if numeric <= 100.0:
            numeric = numeric / 100.0
        else:
            numeric = 1.0

    return clamp(numeric, 0.0, 1.0)


def zone_risk_bias(zone: str) -> float:
    normalized_zone = zone.upper()
    if normalized_zone.startswith("HR") or normalized_zone.endswith("3"):
        return 0.06
    if normalized_zone.startswith("LR") or normalized_zone.endswith("1"):
        return -0.04
    return 0.0
