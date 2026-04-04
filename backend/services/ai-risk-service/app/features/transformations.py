from __future__ import annotations

from typing import Any

import pandas as pd

from app.utils.helpers import clamp


def _float_or_default(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_temporal_features(base_metrics: dict[str, float], temporal_context: dict[str, Any] | None = None) -> dict[str, float]:
    context = temporal_context or {}

    rolling_disruption_3h = clamp(
        _float_or_default(context.get("rolling_disruption_3h"), base_metrics["disruption_freq"])
    )
    traffic_lag_1 = clamp(_float_or_default(context.get("traffic_last_hour"), base_metrics["traffic"]))
    previous_risk_score = clamp(_float_or_default(context.get("previous_risk_score"), 0.5))

    raw_trend = (base_metrics["disruption_freq"] - rolling_disruption_3h) * 0.6 + (
        base_metrics["traffic"] - traffic_lag_1
    ) * 0.4
    risk_trend_1h = clamp(0.5 + (raw_trend * 0.5))

    return {
        "rolling_disruption_3h": rolling_disruption_3h,
        "traffic_lag_1": traffic_lag_1,
        "previous_risk_score": previous_risk_score,
        "risk_trend_1h": risk_trend_1h,
    }


def compute_feature_map(base_metrics: dict[str, float], temporal_context: dict[str, Any] | None = None) -> dict[str, float]:
    disruption_freq = base_metrics["disruption_freq"]
    duration = base_metrics["duration"]
    traffic = base_metrics["traffic"]
    order_drop = base_metrics["order_drop"]
    activity = base_metrics["activity"]
    claims = base_metrics["claims"]

    feature_map = {
        "disruption_freq": disruption_freq,
        "duration": duration,
        "traffic": traffic,
        "order_drop": order_drop,
        "activity": activity,
        "claims": claims,
        "disruption_traffic_interaction": disruption_freq * traffic,
        "exposure_index": (duration * 0.5) + (traffic * 0.5),
        "resilience_gap": 1.0 - activity,
    }
    feature_map.update(compute_temporal_features(base_metrics, temporal_context=temporal_context))
    return feature_map


def append_derived_features(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()

    output["disruption_traffic_interaction"] = output["disruption_freq"] * output["traffic"]
    output["exposure_index"] = (output["duration"] * 0.5) + (output["traffic"] * 0.5)
    output["resilience_gap"] = 1.0 - output["activity"]

    if "rolling_disruption_3h" not in output.columns:
        output["rolling_disruption_3h"] = output["disruption_freq"]
    if "traffic_lag_1" not in output.columns:
        output["traffic_lag_1"] = output["traffic"]
    if "previous_risk_score" not in output.columns:
        output["previous_risk_score"] = 0.5
    if "risk_trend_1h" not in output.columns:
        output["risk_trend_1h"] = 0.5 + ((output["disruption_freq"] - output["rolling_disruption_3h"]) * 0.5)

    output["rolling_disruption_3h"] = output["rolling_disruption_3h"].clip(0.0, 1.0)
    output["traffic_lag_1"] = output["traffic_lag_1"].clip(0.0, 1.0)
    output["previous_risk_score"] = output["previous_risk_score"].clip(0.0, 1.0)
    output["risk_trend_1h"] = output["risk_trend_1h"].clip(0.0, 1.0)

    return output
