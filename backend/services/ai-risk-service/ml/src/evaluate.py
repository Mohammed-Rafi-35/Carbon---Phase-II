from __future__ import annotations

import json
import pickle

import pandas as pd

from ml.src.classification_utils import classification_metrics, risk_score_to_category
from ml.src.common import MODEL_BUNDLE_PATH, TEST_DATA_PATH, TRAIN_DATA_PATH
from ml.src.model_quality import diagnose_fit, regression_metrics


def evaluate_model() -> dict:
    if not MODEL_BUNDLE_PATH.exists():
        raise FileNotFoundError(f"Model artifact missing: {MODEL_BUNDLE_PATH}")
    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(f"Training dataset missing: {TRAIN_DATA_PATH}")
    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(f"Test dataset missing: {TEST_DATA_PATH}")

    with MODEL_BUNDLE_PATH.open("rb") as model_file:
        bundle = pickle.load(model_file)

    model = bundle.get("regressor", bundle["model"])
    scaler = bundle.get("scaler")

    train_dataset = pd.read_csv(TRAIN_DATA_PATH)
    test_dataset = pd.read_csv(TEST_DATA_PATH)

    feature_names = bundle.get("feature_names")
    x_train = train_dataset[feature_names]
    y_train = train_dataset["risk_score"]
    x_test = test_dataset[feature_names]
    y_test = test_dataset["risk_score"]

    transformed_train = scaler.transform(x_train) if scaler is not None else x_train
    transformed_test = scaler.transform(x_test) if scaler is not None else x_test

    train_predictions = model.predict(transformed_train)
    test_predictions = model.predict(transformed_test)

    train_metrics = regression_metrics(y_train.to_numpy(), train_predictions)
    test_metrics = regression_metrics(y_test.to_numpy(), test_predictions)
    fit_quality = diagnose_fit(train_metrics, test_metrics)

    true_train_categories = [risk_score_to_category(float(value)) for value in y_train.to_numpy()]
    true_test_categories = [risk_score_to_category(float(value)) for value in y_test.to_numpy()]
    predicted_train_categories = [risk_score_to_category(float(value)) for value in train_predictions]
    predicted_test_categories = [risk_score_to_category(float(value)) for value in test_predictions]

    classification_report = {
        "train": classification_metrics(true_train_categories, predicted_train_categories),
        "test": classification_metrics(true_test_categories, predicted_test_categories),
    }

    report = {
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "fit_quality": fit_quality,
        "cross_validation": bundle.get("metrics", {}).get("cv", {}),
        "classification": classification_report,
        "feature_importance": bundle.get("metrics", {}).get("feature_importance", {}),
        "feature_importance_validation": bundle.get("metrics", {}).get("feature_importance_validation", {}),
    }
    return report


def main() -> None:
    metrics = evaluate_model()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
