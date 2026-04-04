from __future__ import annotations

import argparse
import json
import pickle

import numpy as np
import pandas as pd

from app.features.feature_builder import FeatureBuilder
from ml.src.common import MODEL_BUNDLE_PATH


def run_prediction(zone: str, metrics: dict[str, float]) -> dict[str, float | str]:
    if not MODEL_BUNDLE_PATH.exists():
        raise FileNotFoundError(f"Model artifact missing: {MODEL_BUNDLE_PATH}")

    with MODEL_BUNDLE_PATH.open("rb") as model_file:
        bundle = pickle.load(model_file)

    regressor = bundle.get("regressor", bundle["model"])
    feature_builder = FeatureBuilder()

    base_metrics = feature_builder.build_base_metrics(metrics)
    feature_map = feature_builder.to_feature_map(base_metrics)
    vector = feature_builder.to_vector(feature_map, bundle.get("feature_names"))

    scaler = bundle.get("scaler")
    transformed = scaler.transform(vector) if scaler is not None else pd.DataFrame(vector, columns=bundle.get("feature_names"))

    prediction = float(regressor.predict(transformed)[0])
    risk_score = float(np.clip(prediction, 0.0, 1.0))

    if risk_score < 0.34:
        category = "LOW"
    elif risk_score < 0.67:
        category = "MEDIUM"
    else:
        category = "HIGH"

    confidence = 0.5
    estimators = getattr(regressor, "estimators_", None)
    if estimators:
        tree_outputs = np.array([float(estimator.predict(transformed)[0]) for estimator in estimators], dtype=float)
        confidence = float(np.clip(1.0 - min(1.0, float(np.std(tree_outputs)) / 0.20), 0.0, 1.0))

    top_factors: list[str] = []
    importances = getattr(regressor, "feature_importances_", None)
    if importances is not None:
        feature_names = bundle.get("feature_names")
        contributions = np.asarray(importances, dtype=float) * np.abs(vector[0])
        ranked = np.argsort(contributions)[::-1][:3]
        top_factors = [feature_names[int(index)] for index in ranked]

    return {
        "zone": zone,
        "risk_score": round(risk_score, 4),
        "risk_category": category,
        "confidence": round(confidence, 4),
        "top_factors": top_factors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Local prediction for AI risk model")
    parser.add_argument("--zone", default="MR-2")
    parser.add_argument("--disruption_freq", type=float, default=0.6)
    parser.add_argument("--duration", type=float, default=0.7)
    parser.add_argument("--traffic", type=float, default=0.5)
    parser.add_argument("--order_drop", type=float, default=0.8)
    parser.add_argument("--activity", type=float, default=0.4)
    parser.add_argument("--claims", type=float, default=0.3)
    args = parser.parse_args()

    metrics = {
        "disruption_freq": args.disruption_freq,
        "duration": args.duration,
        "traffic": args.traffic,
        "order_drop": args.order_drop,
        "activity": args.activity,
        "claims": args.claims,
    }

    output = run_prediction(args.zone, metrics)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
