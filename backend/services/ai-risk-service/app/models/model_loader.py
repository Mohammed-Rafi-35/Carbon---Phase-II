from __future__ import annotations

import pickle
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.core.constants import MODEL_FEATURE_NAMES


logger = logging.getLogger(__name__)


class HeuristicRiskModel:
    def predict(self, x: np.ndarray) -> np.ndarray:
        # This fallback keeps service availability if model artifacts are missing.
        disruption_freq = x[:, 0]
        duration = x[:, 1]
        traffic = x[:, 2]
        order_drop = x[:, 3]
        activity = x[:, 4]
        claims = x[:, 5]

        raw = (
            (0.24 * disruption_freq)
            + (0.16 * duration)
            + (0.18 * traffic)
            + (0.20 * order_drop)
            + (0.14 * claims)
            + (0.08 * (1.0 - activity))
        )
        return np.clip(raw, 0.0, 1.0)


@dataclass(slots=True)
class ModelBundle:
    model: object
    scaler: object | None
    feature_names: list[str]
    model_version: str
    training_metrics: dict[str, object]

    def _to_model_input(self, feature_vector: np.ndarray) -> object:
        transformed: object = feature_vector
        if self.scaler is not None:
            transformed = self.scaler.transform(feature_vector)
        elif hasattr(self.model, "feature_names_in_") and isinstance(feature_vector, np.ndarray):
            transformed = pd.DataFrame(feature_vector, columns=self.feature_names)
        return transformed

    def predict(self, feature_vector: np.ndarray) -> np.ndarray:
        transformed = self._to_model_input(feature_vector)
        predictions = self.model.predict(transformed)
        return np.asarray(predictions, dtype=float)

    def confidence(self, feature_vector: np.ndarray) -> float:
        estimators = getattr(self.model, "estimators_", None)
        if not estimators:
            return 0.5

        transformed = self._to_model_input(feature_vector)
        tree_outputs = []
        for estimator in estimators:
            value = float(estimator.predict(transformed)[0])
            tree_outputs.append(value)

        std_value = float(np.std(tree_outputs))
        normalized = 1.0 - min(1.0, std_value / 0.20)
        return float(np.clip(normalized, 0.0, 1.0))

    def top_factors(self, feature_vector: np.ndarray, top_k: int = 3) -> list[str]:
        importances = getattr(self.model, "feature_importances_", None)
        if importances is None:
            return []

        values = np.asarray(feature_vector[0], dtype=float)
        contributions = np.asarray(importances, dtype=float) * np.abs(values)
        ranked = np.argsort(contributions)[::-1][:top_k]
        return [self.feature_names[int(index)] for index in ranked]


class ModelLoader:
    def __init__(self, model_path: str | None = None) -> None:
        settings = get_settings()
        configured_path = model_path or settings.model_path
        self.model_path = self._resolve_model_path(Path(configured_path), settings)
        if not self.model_path.is_absolute():
            service_root = Path(__file__).resolve().parents[2]
            self.model_path = service_root / self.model_path

        self._bundle: ModelBundle | None = None

    def get_bundle(self) -> ModelBundle:
        if self._bundle is None:
            self._bundle = self._load_or_fallback()
        return self._bundle

    def is_loaded(self) -> bool:
        return self._bundle is not None

    def _load_or_fallback(self) -> ModelBundle:
        if self.model_path.exists():
            try:
                if self.model_path.suffix.lower() == ".pkl":
                    with self.model_path.open("rb") as model_file:
                        payload = pickle.load(model_file)
                else:
                    payload = joblib.load(self.model_path)

                regressor = payload.get("regressor", payload["model"])
                return ModelBundle(
                    model=regressor,
                    scaler=payload.get("scaler"),
                    feature_names=payload.get("feature_names", MODEL_FEATURE_NAMES),
                    model_version=payload.get("model_version", get_settings().model_version),
                    training_metrics=payload.get("metrics", {}),
                )
            except Exception as exc:
                logger.exception("Failed to load model artifact, using fallback model: %s", exc)

        logger.warning("Model artifact not found at %s. Using fallback heuristic model.", self.model_path)
        settings = get_settings()
        return ModelBundle(
            model=HeuristicRiskModel(),
            scaler=None,
            feature_names=MODEL_FEATURE_NAMES,
            model_version=settings.model_version,
            training_metrics={},
        )

    def _resolve_model_path(self, configured_path: Path, settings) -> Path:
        registry_path = Path(settings.model_registry_path)
        if not registry_path.is_absolute():
            service_root = Path(__file__).resolve().parents[2]
            registry_path = service_root / registry_path

        if registry_path.exists():
            try:
                registry = json.loads(registry_path.read_text(encoding="utf-8"))
                active_path = registry.get("active_artifact")
                if active_path:
                    return Path(active_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to read model registry at %s: %s", registry_path, exc)

        return configured_path
