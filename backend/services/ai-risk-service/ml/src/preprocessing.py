from __future__ import annotations

import pandas as pd


NUMERIC_COLUMNS: list[str] = [
    "rainfall",
    "disruption_freq",
    "duration",
    "traffic",
    "order_drop",
    "activity",
    "claims",
    "rolling_disruption_3h",
    "traffic_lag_1",
    "previous_risk_score",
    "risk_trend_1h",
    "risk_score",
]


def preprocess_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    dataset = frame.copy()

    dataset = dataset.drop_duplicates().reset_index(drop=True)

    for column in NUMERIC_COLUMNS:
        dataset[column] = pd.to_numeric(dataset[column], errors="coerce")
        dataset[column] = dataset[column].fillna(dataset[column].median())
        dataset[column] = dataset[column].clip(0.0, 1.0)

    dataset["zone"] = dataset["zone"].fillna("MR-2").astype(str)

    return dataset
