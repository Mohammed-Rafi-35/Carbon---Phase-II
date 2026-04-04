from __future__ import annotations

import numpy as np

from app.core.constants import BASE_FEATURE_NAMES, MODEL_FEATURE_NAMES
from app.features.transformations import compute_feature_map
from app.utils.helpers import normalize_metric


class FeatureBuilder:
    def build_base_metrics(self, metrics: dict[str, float]) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for feature_name in BASE_FEATURE_NAMES:
            normalized[feature_name] = normalize_metric(metrics.get(feature_name))
        return normalized

    def to_feature_map(
        self,
        base_metrics: dict[str, float],
        temporal_context: dict[str, float] | None = None,
    ) -> dict[str, float]:
        return compute_feature_map(base_metrics, temporal_context=temporal_context)

    def to_vector(self, feature_map: dict[str, float], feature_order: list[str] | None = None) -> np.ndarray:
        ordered_features = feature_order or MODEL_FEATURE_NAMES
        values = [feature_map[name] for name in ordered_features]
        return np.array([values], dtype=float)
