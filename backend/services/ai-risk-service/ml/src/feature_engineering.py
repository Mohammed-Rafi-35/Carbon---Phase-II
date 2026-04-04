from __future__ import annotations

import pandas as pd

from app.features.transformations import append_derived_features
from app.core.constants import MODEL_FEATURE_NAMES


TARGET_COLUMN = "risk_score"


def build_feature_frame(dataset: pd.DataFrame) -> pd.DataFrame:
    return append_derived_features(dataset)


def get_training_matrices(feature_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    x = feature_frame[MODEL_FEATURE_NAMES]
    y = feature_frame[TARGET_COLUMN]
    return x, y
