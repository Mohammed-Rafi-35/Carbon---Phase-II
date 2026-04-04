from __future__ import annotations

import math
import os

from app.core.config import get_settings


class FraudMLScorer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None
        self._load_attempted = False

    def score(
        self,
        *,
        gps_valid: bool,
        activity_score: float,
        device_consistency: bool | None,
        severity: str | None,
        event_type: str | None,
        external_risk_score: float | None,
    ) -> float | None:
        if not self.settings.enable_ml:
            return None

        model = self._load_model_if_needed()
        if model is None:
            return None

        feature_vector = [[
            float(1 if gps_valid else 0),
            float(activity_score),
            float(1 if device_consistency is not False else 0),
            self._severity_to_numeric(severity),
            self._event_type_to_numeric(event_type),
            float(external_risk_score or 0.0),
        ]]

        try:
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(feature_vector)
                return float(probabilities[0][1])

            if hasattr(model, "decision_function"):
                raw = float(model.decision_function(feature_vector)[0])
                return 1.0 / (1.0 + math.exp(-raw))

            if hasattr(model, "predict"):
                prediction = model.predict(feature_vector)[0]
                if isinstance(prediction, str):
                    return 1.0 if prediction.upper() in {"ANOMALY", "FRAUD", "FAIL"} else 0.0
                if isinstance(prediction, (int, float)):
                    if prediction in {-1, 1}:
                        return 1.0 if prediction == -1 else 0.0
                    return max(0.0, min(1.0, float(prediction)))
            return None
        except Exception:
            return None

    def _load_model_if_needed(self):
        if self._load_attempted:
            return self._model

        self._load_attempted = True
        model_path = self.settings.model_path.strip()
        if not model_path or not os.path.exists(model_path):
            return None

        try:
            import joblib  # imported lazily so ML remains optional

            self._model = joblib.load(model_path)
        except Exception:
            self._model = None
        return self._model

    @staticmethod
    def _severity_to_numeric(severity: str | None) -> float:
        if not severity:
            return 0.0
        mapping = {
            "LOW": 0.33,
            "MEDIUM": 0.66,
            "HIGH": 1.0,
        }
        return mapping.get(severity.upper(), 0.0)

    @staticmethod
    def _event_type_to_numeric(event_type: str | None) -> float:
        if not event_type:
            return 0.0
        mapping = {
            "WEATHER": 0.2,
            "TRAFFIC": 0.5,
            "PLATFORM": 0.8,
            "SOCIAL": 0.7,
        }
        return mapping.get(event_type.upper(), 0.0)
