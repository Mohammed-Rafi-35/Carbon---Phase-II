from __future__ import annotations

from app.features.feature_builder import FeatureBuilder


def test_feature_builder_normalizes_and_expands_metrics() -> None:
    builder = FeatureBuilder()

    base = builder.build_base_metrics(
        {
            "disruption_freq": 60,
            "duration": 0.7,
            "traffic": 0.5,
            "order_drop": 80,
            "activity": 0.4,
            "claims": 0.3,
        }
    )

    assert base["disruption_freq"] == 0.6
    assert base["order_drop"] == 0.8

    feature_map = builder.to_feature_map(base)
    vector = builder.to_vector(feature_map)

    assert vector.shape == (1, 13)
    assert float(vector[0, 6]) == base["disruption_freq"] * base["traffic"]
