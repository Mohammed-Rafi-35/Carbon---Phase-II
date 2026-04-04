from __future__ import annotations

import json
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ml.src.common import (
    EVALUATION_REPORT_PATH,
    METADATA_PATH,
    MODEL_BUNDLE_PATH,
    TEST_DATA_PATH,
    TRAIN_DATA_PATH,
)


def _load_bundle() -> dict:
    if not MODEL_BUNDLE_PATH.exists():
        raise FileNotFoundError(f"Model artifact missing: {MODEL_BUNDLE_PATH}")
    with MODEL_BUNDLE_PATH.open("rb") as model_file:
        return pickle.load(model_file)


def _safe_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def generate_visuals() -> Path:
    if not TRAIN_DATA_PATH.exists() or not TEST_DATA_PATH.exists():
        raise FileNotFoundError("Train/test data not found. Run training first.")

    bundle = _load_bundle()
    model = bundle.get("regressor", bundle["model"])
    scaler = bundle.get("scaler")
    feature_names = bundle.get("feature_names")

    train_df = pd.read_csv(TRAIN_DATA_PATH)
    test_df = pd.read_csv(TEST_DATA_PATH)

    x_train = train_df[feature_names]
    y_train = train_df["risk_score"]
    x_test = test_df[feature_names]
    y_test = test_df["risk_score"]

    transformed_train = scaler.transform(x_train) if scaler is not None else x_train
    transformed_test = scaler.transform(x_test) if scaler is not None else x_test

    train_pred = model.predict(transformed_train)
    test_pred = model.predict(transformed_test)

    reports_dir = MODEL_BUNDLE_PATH.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")

    # 1) Predicted vs Actual
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(y_test, test_pred, alpha=0.35, s=12, label="Test")
    axis_min = min(float(y_test.min()), float(test_pred.min()))
    axis_max = max(float(y_test.max()), float(test_pred.max()))
    ax.plot([axis_min, axis_max], [axis_min, axis_max], linestyle="--", linewidth=1.2, color="black")
    ax.set_title("AI Risk: Predicted vs Actual (Test)")
    ax.set_xlabel("Actual Risk Score")
    ax.set_ylabel("Predicted Risk Score")
    ax.legend()
    fig.tight_layout()
    fig.savefig(reports_dir / "predicted_vs_actual_test.png", dpi=160)
    plt.close(fig)

    # 2) Residual distribution
    residuals = y_test.to_numpy() - test_pred
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.histplot(residuals, kde=True, bins=35, ax=ax)
    ax.set_title("AI Risk: Residual Distribution (Test)")
    ax.set_xlabel("Residual (Actual - Predicted)")
    fig.tight_layout()
    fig.savefig(reports_dir / "residual_distribution_test.png", dpi=160)
    plt.close(fig)

    # 3) Feature importance
    importances = getattr(model, "feature_importances_", None)
    if importances is not None:
        importance_df = (
            pd.DataFrame({"feature": feature_names, "importance": importances})
            .sort_values("importance", ascending=False)
            .head(12)
        )
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=importance_df, x="importance", y="feature", orient="h", ax=ax)
        ax.set_title("AI Risk: Top Feature Importances")
        ax.set_xlabel("Importance")
        ax.set_ylabel("Feature")
        fig.tight_layout()
        fig.savefig(reports_dir / "feature_importance_top12.png", dpi=160)
        plt.close(fig)

    # 4) Metric summary chart from metadata/evaluation report
    metadata = _safe_json(METADATA_PATH)
    evaluation = _safe_json(EVALUATION_REPORT_PATH)

    train_metrics = metadata.get("train_metrics", evaluation.get("train_metrics", {}))
    test_metrics = metadata.get("metrics", evaluation.get("test_metrics", {}))

    metric_rows = []
    for metric_name in ["mae", "rmse", "r2"]:
        if metric_name in train_metrics and metric_name in test_metrics:
            metric_rows.append({"metric": metric_name.upper(), "split": "Train", "value": train_metrics[metric_name]})
            metric_rows.append({"metric": metric_name.upper(), "split": "Test", "value": test_metrics[metric_name]})

    if metric_rows:
        metrics_df = pd.DataFrame(metric_rows)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(data=metrics_df, x="metric", y="value", hue="split", ax=ax)
        ax.set_title("AI Risk: Train vs Test Metrics")
        ax.set_xlabel("Metric")
        ax.set_ylabel("Value")
        fig.tight_layout()
        fig.savefig(reports_dir / "metric_summary_train_test.png", dpi=160)
        plt.close(fig)

    return reports_dir


def main() -> None:
    output_dir = generate_visuals()
    print(f"Visual evaluation artifacts generated at: {output_dir}")


if __name__ == "__main__":
    main()
