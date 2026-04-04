from __future__ import annotations

import pandas as pd

from app.repositories.feedback_repository import FeedbackRepository
from ml.src.classification_utils import risk_score_to_category
from ml.src.common import FEEDBACK_DATASET_PATH, ensure_dirs


LABEL_TO_SCORE = {
    "LOW": 0.20,
    "MEDIUM": 0.50,
    "HIGH": 0.80,
}


def build_feedback_dataset() -> pd.DataFrame:
    ensure_dirs()

    repository = FeedbackRepository()
    rows = repository.reviewed_feedback_rows()

    labeled_rows: list[dict[str, float | str]] = []
    for row in rows:
        features = row["features"]

        actual_outcome = row.get("actual_outcome")
        corrected_label = row.get("corrected_label")
        if actual_outcome is not None:
            risk_score = float(actual_outcome)
        elif corrected_label:
            risk_score = float(LABEL_TO_SCORE.get(str(corrected_label).upper(), 0.5))
        else:
            continue

        output = {
            "zone": row.get("zone", "MR-2"),
            "disruption_freq": float(features.get("disruption_freq", 0.5)),
            "duration": float(features.get("duration", 0.5)),
            "traffic": float(features.get("traffic", 0.5)),
            "order_drop": float(features.get("order_drop", 0.5)),
            "activity": float(features.get("activity", 0.5)),
            "claims": float(features.get("claims", 0.5)),
            "rolling_disruption_3h": float(features.get("rolling_disruption_3h", features.get("disruption_freq", 0.5))),
            "traffic_lag_1": float(features.get("traffic_lag_1", features.get("traffic", 0.5))),
            "previous_risk_score": float(features.get("previous_risk_score", 0.5)),
            "risk_trend_1h": float(features.get("risk_trend_1h", 0.5)),
            "risk_score": risk_score,
            "risk_category": risk_score_to_category(risk_score),
        }
        labeled_rows.append(output)

    frame = pd.DataFrame(labeled_rows)
    if not frame.empty:
        frame.to_csv(FEEDBACK_DATASET_PATH, index=False)
    return frame


def main() -> None:
    frame = build_feedback_dataset()
    print(f"Feedback rows exported: {len(frame)} -> {FEEDBACK_DATASET_PATH}")


if __name__ == "__main__":
    main()
