from __future__ import annotations

from dataclasses import dataclass
import os

import numpy as np


os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./ai_risk_unit_test.db"

from app.schemas.risk_schema import RiskEvaluateRequest, RiskMetrics
from app.db.base import Base
from app.db.session import engine
from app.services.inference_service import InferenceService


Base.metadata.create_all(bind=engine)


@dataclass(slots=True)
class _StubBundle:
    feature_names: list[str]
    model_version: str

    def predict(self, _: np.ndarray) -> np.ndarray:
        return np.array([0.72], dtype=float)

    def confidence(self, _: np.ndarray) -> float:
        return 0.8

    def top_factors(self, _: np.ndarray) -> list[str]:
        return ["order_drop", "traffic", "disruption_freq"]


class _StubLoader:
    def __init__(self) -> None:
        self._bundle = _StubBundle(
            feature_names=[
                "disruption_freq",
                "duration",
                "traffic",
                "order_drop",
                "activity",
                "claims",
                "disruption_traffic_interaction",
                "exposure_index",
                "resilience_gap",
                "rolling_disruption_3h",
                "traffic_lag_1",
                "previous_risk_score",
                "risk_trend_1h",
            ],
            model_version="v-test",
        )

    def get_bundle(self) -> _StubBundle:
        return self._bundle

    def is_loaded(self) -> bool:
        return True


def test_inference_service_produces_expected_shape() -> None:
    service = InferenceService(model_loader=_StubLoader())
    request = RiskEvaluateRequest(
        zone="MR-2",
        metrics=RiskMetrics(
            disruption_freq=0.6,
            duration=0.7,
            traffic=0.5,
            order_drop=0.8,
            activity=0.4,
            claims=0.3,
        ),
    )

    result = service.evaluate(request)

    assert result.model_version == "v-test"
    assert result.risk_category == "HIGH"
    assert 1.0 <= result.premium_multiplier <= 1.5
