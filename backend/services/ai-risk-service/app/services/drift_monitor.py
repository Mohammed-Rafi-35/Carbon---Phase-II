from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from app.core.constants import MODEL_FEATURE_NAMES
from app.repositories.feedback_repository import FeedbackRepository


class DriftMonitor:
    def __init__(self, metadata_path: str | Path, feedback_repository: FeedbackRepository) -> None:
        self.metadata_path = Path(metadata_path)
        self.feedback_repository = feedback_repository

    def evaluate(self, *, sample_size: int = 300, z_threshold: float = 2.5) -> dict[str, Any]:
        baseline = self._load_baseline()
        if baseline is None:
            return {
                "status": "unknown",
                "message": "Training baseline statistics are unavailable.",
                "sample_size": 0,
                "alerts": [],
            }

        recent = self.feedback_repository.recent_feature_payloads(limit=sample_size)
        if not recent:
            return {
                "status": "unknown",
                "message": "No prediction logs available yet.",
                "sample_size": 0,
                "alerts": [],
            }

        alerts: list[dict[str, float | str]] = []
        feature_stats = baseline.get("feature_stats", {})

        for feature_name in MODEL_FEATURE_NAMES:
            baseline_stats = feature_stats.get(feature_name)
            if not baseline_stats:
                continue

            values = [float(item["features"].get(feature_name, 0.0)) for item in recent]
            recent_mean = float(np.mean(values))
            baseline_mean = float(baseline_stats.get("mean", 0.0))
            baseline_std = float(baseline_stats.get("std", 0.0))
            z_score = abs(recent_mean - baseline_mean) / max(baseline_std, 1e-6)

            if z_score >= z_threshold:
                alerts.append(
                    {
                        "feature": feature_name,
                        "recent_mean": recent_mean,
                        "baseline_mean": baseline_mean,
                        "z_score": float(z_score),
                    }
                )

        prediction_baseline = baseline.get("prediction_stats", {})
        if prediction_baseline:
            prediction_values = [float(item["risk_score"]) for item in recent]
            recent_pred_mean = float(np.mean(prediction_values))
            base_pred_mean = float(prediction_baseline.get("mean", 0.0))
            base_pred_std = float(prediction_baseline.get("std", 0.0))
            pred_z = abs(recent_pred_mean - base_pred_mean) / max(base_pred_std, 1e-6)
            if pred_z >= z_threshold:
                alerts.append(
                    {
                        "feature": "risk_score",
                        "recent_mean": recent_pred_mean,
                        "baseline_mean": base_pred_mean,
                        "z_score": float(pred_z),
                    }
                )

        status = "stable" if not alerts else "drift_detected"
        return {
            "status": status,
            "message": "No meaningful drift detected." if status == "stable" else "Feature drift alerts found.",
            "sample_size": len(recent),
            "alerts": alerts,
        }

    def _load_baseline(self) -> dict[str, Any] | None:
        if not self.metadata_path.exists():
            return None
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return {
            "feature_stats": data.get("feature_stats", {}),
            "prediction_stats": data.get("prediction_stats", {}),
        }
