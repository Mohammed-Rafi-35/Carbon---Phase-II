from __future__ import annotations

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


RISK_LABELS: list[str] = ["LOW", "MEDIUM", "HIGH"]


def risk_score_to_category(score: float, low_threshold: float = 0.34, high_threshold: float = 0.67) -> str:
    if score < low_threshold:
        return "LOW"
    if score < high_threshold:
        return "MEDIUM"
    return "HIGH"


def classification_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }
