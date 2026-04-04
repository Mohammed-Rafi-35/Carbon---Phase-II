from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal
from app.models.prediction_log import PredictionLog


class FeedbackRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self.session_factory = session_factory or SessionLocal

    def log_prediction(
        self,
        *,
        zone: str,
        input_features: dict[str, float],
        risk_score: float,
        risk_category: str,
        premium_multiplier: float,
        confidence: float,
        model_version: str,
        top_factors: list[str],
    ) -> int:
        with self.session_factory() as session:
            row = PredictionLog(
                created_at=datetime.now(tz=timezone.utc),
                zone=zone,
                input_features=input_features,
                risk_score=float(risk_score),
                risk_category=risk_category,
                premium_multiplier=float(premium_multiplier),
                confidence=float(confidence),
                model_version=model_version,
                top_factors=top_factors,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return int(row.id)

    def submit_feedback(
        self,
        *,
        prediction_id: int,
        actual_outcome: float | None,
        corrected_label: str | None,
        review_notes: str | None,
    ) -> bool:
        with self.session_factory() as session:
            row = session.get(PredictionLog, prediction_id)
            if row is None:
                return False
            row.actual_outcome = actual_outcome
            row.corrected_label = corrected_label
            row.review_status = "reviewed"
            row.review_notes = review_notes
            row.corrected_at = datetime.now(tz=timezone.utc)
            session.add(row)
            session.commit()
            return True

    def list_prediction_logs(self, *, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            stmt = select(PredictionLog)
            if status:
                stmt = stmt.where(PredictionLog.review_status == status)
            stmt = stmt.order_by(desc(PredictionLog.id)).limit(limit)
            rows = list(session.execute(stmt).scalars().all())

        return [
            {
                "id": int(row.id),
                "created_at": row.created_at.isoformat(),
                "zone": row.zone,
                "risk_score": float(row.risk_score),
                "risk_category": row.risk_category,
                "confidence": float(row.confidence),
                "model_version": row.model_version,
                "review_status": row.review_status,
            }
            for row in rows
        ]

    def recent_feature_payloads(self, *, limit: int = 500) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            stmt = select(PredictionLog.input_features, PredictionLog.risk_score).order_by(desc(PredictionLog.id)).limit(limit)
            rows = list(session.execute(stmt).all())

        payloads: list[dict[str, Any]] = []
        for features, risk_score in rows:
            if not isinstance(features, dict):
                continue
            payloads.append({"features": features, "risk_score": float(risk_score)})
        return payloads

    def reviewed_feedback_rows(self) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            stmt = (
                select(
                    PredictionLog.id,
                    PredictionLog.zone,
                    PredictionLog.input_features,
                    PredictionLog.actual_outcome,
                    PredictionLog.corrected_label,
                )
                .where(
                    PredictionLog.review_status == "reviewed",
                    (PredictionLog.actual_outcome.is_not(None) | PredictionLog.corrected_label.is_not(None)),
                )
                .order_by(PredictionLog.id.asc())
            )
            rows = list(session.execute(stmt).all())

        output: list[dict[str, Any]] = []
        for row_id, zone, features, actual_outcome, corrected_label in rows:
            if not isinstance(features, dict):
                continue
            output.append(
                {
                    "id": int(row_id),
                    "zone": zone,
                    "features": features,
                    "actual_outcome": actual_outcome,
                    "corrected_label": corrected_label,
                }
            )
        return output
