from __future__ import annotations

from app.core.config import get_settings
from app.core.constants import RISK_CLASSIFICATION_STRATEGY, RiskCategory
from app.features.feature_builder import FeatureBuilder
from app.integrations.realtime_signals import PublicSignalClient
from app.models.model_loader import ModelLoader
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.risk_schema import FeedbackRequest, RiskEvaluateData, RiskEvaluateRequest
from app.services.drift_monitor import DriftMonitor
from app.utils.helpers import clamp, zone_risk_bias


class InferenceService:
    def __init__(
        self,
        model_loader: ModelLoader | None = None,
        feature_builder: FeatureBuilder | None = None,
        signal_client: PublicSignalClient | None = None,
    ) -> None:
        self.settings = get_settings()
        self.model_loader = model_loader or ModelLoader()
        self.feature_builder = feature_builder or FeatureBuilder()
        self.signal_client = signal_client or PublicSignalClient()

        self.feedback_repository = FeedbackRepository()
        self.drift_monitor = DriftMonitor(metadata_path=self.settings.metadata_path, feedback_repository=self.feedback_repository)

    def evaluate(self, request: RiskEvaluateRequest) -> RiskEvaluateData:
        bundle = self.model_loader.get_bundle()

        base_metrics = self.feature_builder.build_base_metrics(request.metrics.model_dump())
        if self.settings.enable_external_signals:
            base_metrics = self.signal_client.blend_with_metrics(request.zone, base_metrics)

        context = request.context.model_dump(exclude_none=True) if request.context else None
        feature_map = self.feature_builder.to_feature_map(base_metrics, temporal_context=context)
        feature_vector = self.feature_builder.to_vector(feature_map, bundle.feature_names)

        model_prediction = float(bundle.predict(feature_vector)[0])
        adjusted_ml = clamp(model_prediction + zone_risk_bias(request.zone))

        rule_prediction = self._rule_risk_score(base_metrics, feature_map, request.zone)
        hybrid_prediction = clamp((0.7 * adjusted_ml) + (0.3 * rule_prediction))

        risk_category = self._classify(hybrid_prediction)
        premium_multiplier = self._premium_multiplier(hybrid_prediction)
        confidence = round(bundle.confidence(feature_vector), 4)
        top_factors = bundle.top_factors(feature_vector)

        prediction_id = self.feedback_repository.log_prediction(
            zone=request.zone,
            input_features=feature_map,
            risk_score=hybrid_prediction,
            risk_category=risk_category,
            premium_multiplier=premium_multiplier,
            confidence=confidence,
            model_version=bundle.model_version,
            top_factors=top_factors,
        )

        return RiskEvaluateData(
            risk_score=round(hybrid_prediction, 4),
            risk_category=risk_category,
            premium_multiplier=premium_multiplier,
            confidence=confidence,
            top_factors=top_factors,
            prediction_id=prediction_id,
            model_version=bundle.model_version,
        )

    def health(self) -> dict[str, object]:
        bundle = self.model_loader.get_bundle()
        drift = self.drift_monitor.evaluate()
        return {
            "status": "healthy",
            "model_version": bundle.model_version,
            "model_loaded": self.model_loader.is_loaded(),
            "classification_strategy": RISK_CLASSIFICATION_STRATEGY,
            "drift_status": drift.get("status"),
        }

    def submit_feedback(self, feedback: FeedbackRequest) -> bool:
        return self.feedback_repository.submit_feedback(
            prediction_id=feedback.prediction_id,
            actual_outcome=feedback.actual_outcome,
            corrected_label=feedback.corrected_label,
            review_notes=feedback.review_notes,
        )

    def list_feedback(self, *, status: str | None = None, limit: int = 50) -> list[dict[str, object]]:
        return self.feedback_repository.list_prediction_logs(status=status, limit=limit)

    def drift_report(self) -> dict[str, object]:
        return self.drift_monitor.evaluate()

    def _classify(self, risk_score: float) -> str:
        if risk_score < self.settings.low_risk_threshold:
            return RiskCategory.LOW
        if risk_score < self.settings.high_risk_threshold:
            return RiskCategory.MEDIUM
        return RiskCategory.HIGH

    def _premium_multiplier(self, risk_score: float) -> float:
        raw = self.settings.premium_multiplier_base + (risk_score * self.settings.premium_multiplier_sensitivity)
        bounded = min(self.settings.premium_multiplier_cap, raw)
        return round(bounded, 2)

    def _rule_risk_score(self, base_metrics: dict[str, float], feature_map: dict[str, float], zone: str) -> float:
        rule_score = (
            (0.24 * base_metrics["disruption_freq"])
            + (0.18 * base_metrics["duration"])
            + (0.17 * base_metrics["traffic"])
            + (0.18 * base_metrics["order_drop"])
            + (0.15 * base_metrics["claims"])
            + (0.08 * feature_map["rolling_disruption_3h"])
            + (0.05 * feature_map["risk_trend_1h"])
            - (0.07 * base_metrics["activity"])
        )
        return clamp(rule_score + zone_risk_bias(zone))
