from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ml.src.common import RAW_DATA_PATH, ensure_dirs


@dataclass(slots=True)
class DataGenerationConfig:
    n_samples: int = 12000
    random_seed: int = 42


SCENARIOS: dict[str, dict[str, float]] = {
    "normal": {
        "rain_alpha": 1.6,
        "rain_beta": 4.5,
        "traffic_bias": 0.35,
        "disruption_bias": 0.30,
        "zone_hr_probability": 0.12,
    },
    "traffic_congestion": {
        "rain_alpha": 2.0,
        "rain_beta": 3.7,
        "traffic_bias": 0.70,
        "disruption_bias": 0.58,
        "zone_hr_probability": 0.28,
    },
    "heavy_rain": {
        "rain_alpha": 4.8,
        "rain_beta": 1.9,
        "traffic_bias": 0.78,
        "disruption_bias": 0.82,
        "zone_hr_probability": 0.52,
    },
    "platform_outage": {
        "rain_alpha": 1.5,
        "rain_beta": 3.4,
        "traffic_bias": 0.62,
        "disruption_bias": 0.90,
        "zone_hr_probability": 0.44,
    },
}

SCENARIO_WEIGHTS = {
    "normal": 0.45,
    "traffic_congestion": 0.25,
    "heavy_rain": 0.20,
    "platform_outage": 0.10,
}


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _simulate_risk_score(
    disruption_freq: float,
    duration: float,
    traffic: float,
    order_drop: float,
    activity: float,
    claims: float,
    *,
    rolling_disruption_3h: float,
    previous_risk_score: float,
    risk_trend_1h: float,
    rng: np.random.Generator,
) -> float:
    nonlinear_component = (0.10 * (disruption_freq**2)) + (0.05 * traffic * order_drop)
    temporal_component = (
        (0.14 * rolling_disruption_3h)
        + (0.16 * previous_risk_score)
        + (0.12 * risk_trend_1h)
    )
    base_score = (
        (0.20 * disruption_freq)
        + (0.15 * duration)
        + (0.16 * traffic)
        + (0.18 * order_drop)
        + (0.14 * claims)
        + (0.10 * (1.0 - activity))
        + nonlinear_component
        + temporal_component
    )

    noise = float(rng.normal(loc=0.0, scale=0.025))
    return _clamp(base_score + noise)


def generate_synthetic_dataset(config: DataGenerationConfig | None = None) -> pd.DataFrame:
    cfg = config or DataGenerationConfig()
    rng = np.random.default_rng(cfg.random_seed)

    scenario_names = list(SCENARIO_WEIGHTS.keys())
    scenario_probabilities = np.array(list(SCENARIO_WEIGHTS.values()), dtype=float)

    zone_state = {
        "LR-1": {"prev_traffic": 0.35, "prev_risk": 0.30, "disruption_history": [0.30, 0.35]},
        "MR-2": {"prev_traffic": 0.50, "prev_risk": 0.45, "disruption_history": [0.45, 0.50]},
        "HR-3": {"prev_traffic": 0.66, "prev_risk": 0.62, "disruption_history": [0.58, 0.64]},
    }

    rows: list[dict[str, float | str]] = []
    for _ in range(cfg.n_samples):
        scenario_name = str(rng.choice(scenario_names, p=scenario_probabilities))
        scenario = SCENARIOS[scenario_name]

        rainfall = _clamp(float(rng.beta(scenario["rain_alpha"], scenario["rain_beta"])))
        disruption_freq = _clamp(
            (0.75 * rainfall)
            + (0.18 * scenario["disruption_bias"])
            + float(rng.normal(0, 0.05))
        )
        duration = _clamp((0.70 * rainfall) + (0.20 * disruption_freq) + float(rng.normal(0, 0.05)))
        traffic = _clamp((0.60 * rainfall) + (0.25 * scenario["traffic_bias"]) + float(rng.normal(0, 0.07)))
        order_drop = _clamp((0.80 * rainfall) + (0.15 * traffic) + float(rng.normal(0, 0.06)))
        activity = _clamp(
            1.0
            - (0.58 * disruption_freq + 0.22 * duration + 0.08 * rainfall)
            + float(rng.normal(0, 0.06))
        )
        claims = _clamp((0.50 * order_drop) + (0.25 * disruption_freq) + (0.13 * rainfall) + float(rng.normal(0, 0.04)))

        hr_prob = scenario["zone_hr_probability"]
        zones = ["LR-1", "MR-2", "HR-3"]
        zone_probs = np.array([max(0.12, 0.55 - hr_prob), max(0.18, 0.33), min(0.70, hr_prob)], dtype=float)
        zone_probs = zone_probs / zone_probs.sum()
        zone = str(rng.choice(zones, p=zone_probs))

        state = zone_state[zone]
        traffic_lag_1 = float(state["prev_traffic"])
        previous_risk_score = float(state["prev_risk"])

        disruption_history = list(state["disruption_history"])
        rolling_disruption_3h = _clamp(float(np.mean(disruption_history[-2:] + [disruption_freq])))

        raw_trend = (disruption_freq - rolling_disruption_3h) * 0.6 + (traffic - traffic_lag_1) * 0.4
        risk_trend_1h = _clamp(0.5 + (raw_trend * 0.5))

        risk_score = _simulate_risk_score(
            disruption_freq,
            duration,
            traffic,
            order_drop,
            activity,
            claims,
            rolling_disruption_3h=rolling_disruption_3h,
            previous_risk_score=previous_risk_score,
            risk_trend_1h=risk_trend_1h,
            rng=rng,
        )

        state["prev_traffic"] = traffic
        state["prev_risk"] = risk_score
        disruption_history.append(disruption_freq)
        if len(disruption_history) > 3:
            disruption_history = disruption_history[-3:]
        state["disruption_history"] = disruption_history

        rows.append(
            {
                "scenario": scenario_name,
                "zone": zone,
                "rainfall": rainfall,
                "disruption_freq": disruption_freq,
                "duration": duration,
                "traffic": traffic,
                "order_drop": order_drop,
                "activity": activity,
                "claims": claims,
                "rolling_disruption_3h": rolling_disruption_3h,
                "traffic_lag_1": traffic_lag_1,
                "previous_risk_score": previous_risk_score,
                "risk_trend_1h": risk_trend_1h,
                "risk_score": risk_score,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    frame = generate_synthetic_dataset()
    frame.to_csv(RAW_DATA_PATH, index=False)
    print(f"Synthetic dataset generated: {RAW_DATA_PATH} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
