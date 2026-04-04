from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_validate, train_test_split

from ml.src.classification_utils import classification_metrics, risk_score_to_category
from ml.src.common import (
    DEFAULT_TRAINING_CONFIG_PATH,
    EVALUATION_REPORT_PATH,
    FEEDBACK_DATASET_PATH,
    METADATA_PATH,
    MODEL_BUNDLE_PATH,
    MODEL_REGISTRY_PATH,
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
    TEST_DATA_PATH,
    TRAIN_DATA_PATH,
    ensure_dirs,
)
from ml.src.data_generation import DataGenerationConfig, generate_synthetic_dataset
from ml.src.feature_engineering import get_training_matrices, build_feature_frame
from ml.src.model_quality import diagnose_fit, regression_metrics, summarize_cv
from ml.src.model_registry import register_artifact
from ml.src.preprocessing import preprocess_dataset


def load_training_config(config_path=DEFAULT_TRAINING_CONFIG_PATH) -> dict:
    if not config_path.exists():
        return {
            "dataset": {"samples": 12000, "random_seed": 42, "test_size": 0.2},
            "evaluation": {
                "cv_folds": 5,
                "min_test_r2": 0.75,
                "max_r2_gap": 0.08,
                "max_rmse_ratio": 1.4,
            },
            "model": {
                "version": "v1",
                "n_estimators": 240,
                "max_depth": 8,
                "min_samples_split": 14,
                "min_samples_leaf": 10,
                "random_state": 42,
            },
            "feedback": {
                "include": True,
                "min_rows": 20,
            },
        }

    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _build_model(cfg: dict) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=int(cfg.get("n_estimators", 240)),
        max_depth=int(cfg.get("max_depth", 8)),
        min_samples_split=int(cfg.get("min_samples_split", 14)),
        min_samples_leaf=int(cfg.get("min_samples_leaf", 10)),
        random_state=int(cfg.get("random_state", 42)),
        n_jobs=1,
    )


def _threshold_categories(values: np.ndarray) -> list[str]:
    return [risk_score_to_category(float(value)) for value in values]


def _feature_stats(features: pd.DataFrame) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    for feature_name in features.columns:
        series = features[feature_name]
        stats[feature_name] = {
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
            "min": float(series.min()),
            "max": float(series.max()),
        }
    return stats


def _importance_validation(feature_importance: dict[str, float]) -> dict[str, object]:
    disruption_weight = (
        feature_importance.get("disruption_freq", 0.0)
        + feature_importance.get("order_drop", 0.0)
        + feature_importance.get("traffic", 0.0)
        + feature_importance.get("rolling_disruption_3h", 0.0)
    )
    activity_weight = feature_importance.get("activity", 0.0)

    checks = {
        "disruption_dominance": disruption_weight >= activity_weight,
        "temporal_signal_present": feature_importance.get("rolling_disruption_3h", 0.0)
        + feature_importance.get("previous_risk_score", 0.0)
        > 0.02,
    }

    failures = [name for name, passed in checks.items() if not passed]
    return {
        "checks": checks,
        "status": "passed" if not failures else "warning",
        "failures": failures,
    }


def _load_feedback_dataset(config: dict) -> pd.DataFrame | None:
    feedback_cfg = config.get("feedback", {})
    include_feedback = bool(feedback_cfg.get("include", True))
    minimum_rows = int(feedback_cfg.get("min_rows", 20))

    if not include_feedback or not FEEDBACK_DATASET_PATH.exists():
        return None

    feedback_data = pd.read_csv(FEEDBACK_DATASET_PATH)
    if len(feedback_data) < minimum_rows:
        return None

    return feedback_data


def train_model() -> dict:
    ensure_dirs()
    config = load_training_config()

    dataset_cfg = config.get("dataset", {})
    evaluation_cfg = config.get("evaluation", {})
    model_cfg = config.get("model", {})

    synthetic_dataset = generate_synthetic_dataset(
        DataGenerationConfig(
            n_samples=int(dataset_cfg.get("samples", 12000)),
            random_seed=int(dataset_cfg.get("random_seed", 42)),
        )
    )

    feedback_dataset = _load_feedback_dataset(config)
    if feedback_dataset is not None:
        synthetic_dataset = pd.concat([synthetic_dataset, feedback_dataset], ignore_index=True)

    synthetic_dataset.to_csv(RAW_DATA_PATH, index=False)

    processed_dataset = preprocess_dataset(synthetic_dataset)
    processed_dataset.to_csv(PROCESSED_DATA_PATH, index=False)

    feature_frame = build_feature_frame(processed_dataset)
    x, y = get_training_matrices(feature_frame)
    y_class = y.apply(risk_score_to_category)

    x_train, x_test, y_train, y_test, y_class_train, y_class_test = train_test_split(
        x,
        y,
        y_class,
        test_size=float(dataset_cfg.get("test_size", 0.2)),
        random_state=int(model_cfg.get("random_state", 42)),
        shuffle=True,
        stratify=y_class,
    )

    train_export = x_train.copy()
    train_export["risk_score"] = y_train.to_numpy()
    train_export["risk_category"] = y_class_train.to_numpy()
    train_export.to_csv(TRAIN_DATA_PATH, index=False)

    test_export = x_test.copy()
    test_export["risk_score"] = y_test.to_numpy()
    test_export["risk_category"] = y_class_test.to_numpy()
    test_export.to_csv(TEST_DATA_PATH, index=False)

    model = _build_model(model_cfg)
    model.fit(x_train, y_train)

    cv_folds = int(evaluation_cfg.get("cv_folds", 5))
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=int(model_cfg.get("random_state", 42)))
    cv_results = cross_validate(
        _build_model(model_cfg),
        x_train,
        y_train,
        cv=cv,
        scoring={"mae": "neg_mean_absolute_error", "rmse": "neg_root_mean_squared_error", "r2": "r2"},
        n_jobs=1,
    )
    cv_summary = summarize_cv(cv_results)

    train_predictions = model.predict(x_train)
    test_predictions = model.predict(x_test)

    train_metrics = regression_metrics(y_train.to_numpy(), train_predictions)
    test_metrics = regression_metrics(y_test.to_numpy(), test_predictions)

    fit_quality = diagnose_fit(
        train_metrics,
        test_metrics,
        min_test_r2=float(evaluation_cfg.get("min_test_r2", 0.75)),
        max_r2_gap=float(evaluation_cfg.get("max_r2_gap", 0.08)),
        max_rmse_ratio=float(evaluation_cfg.get("max_rmse_ratio", 1.4)),
    )

    class_train_pred = _threshold_categories(train_predictions)
    class_test_pred = _threshold_categories(test_predictions)
    classification_train_metrics = classification_metrics(list(y_class_train), class_train_pred)
    classification_test_metrics = classification_metrics(list(y_class_test), class_test_pred)

    feature_importance = {
        feature_name: float(value)
        for feature_name, value in zip(x.columns, model.feature_importances_, strict=True)
    }
    importance_validation = _importance_validation(feature_importance)

    train_and_test_predictions = np.concatenate([train_predictions, test_predictions])
    prediction_stats = {
        "mean": float(np.mean(train_and_test_predictions)),
        "std": float(np.std(train_and_test_predictions)),
        "min": float(np.min(train_and_test_predictions)),
        "max": float(np.max(train_and_test_predictions)),
    }
    feature_stats = _feature_stats(pd.concat([x_train, x_test], ignore_index=True))

    bundle = {
        "model": model,
        "regressor": model,
        "scaler": None,
        "feature_names": list(x.columns),
        "model_version": model_cfg.get("version", "v1"),
        "classification_strategy": "thresholds",
        "metrics": {
            "regression": {
                "train": train_metrics,
                "test": test_metrics,
                "cv": cv_summary,
                "fit_quality": fit_quality,
            },
            "classification": {
                "train": classification_train_metrics,
                "test": classification_test_metrics,
            },
            "feature_importance": feature_importance,
            "feature_importance_validation": importance_validation,
            "train": train_metrics,
            "test": test_metrics,
            "cv": cv_summary,
            "fit_quality": fit_quality,
        },
    }

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    version = str(bundle["model_version"])
    versioned_artifact = MODEL_BUNDLE_PATH.parent / f"risk_model_{version}_{timestamp}.pkl"

    with versioned_artifact.open("wb") as model_file:
        pickle.dump(bundle, model_file, protocol=pickle.HIGHEST_PROTOCOL)
    with MODEL_BUNDLE_PATH.open("wb") as model_file:
        pickle.dump(bundle, model_file, protocol=pickle.HIGHEST_PROTOCOL)

    registry = register_artifact(
        registry_path=MODEL_REGISTRY_PATH,
        artifact_path=versioned_artifact.resolve(),
        model_version=version,
        metrics=test_metrics,
    )

    metadata = {
        "version": bundle["model_version"],
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "artifact": MODEL_BUNDLE_PATH.name,
        "versioned_artifact": str(versioned_artifact),
        "classification_strategy": "thresholds",
        "training_rows": int(len(x_train)),
        "validation_rows": int(len(x_test)),
        "features": list(x.columns),
        "metrics": test_metrics,
        "train_metrics": train_metrics,
        "classification_metrics": {
            "train": classification_train_metrics,
            "test": classification_test_metrics,
        },
        "cross_validation": cv_summary,
        "fit_quality": fit_quality,
        "feature_importance": feature_importance,
        "feature_importance_validation": importance_validation,
        "feature_stats": feature_stats,
        "prediction_stats": prediction_stats,
        "feedback_rows_used": 0 if feedback_dataset is None else int(len(feedback_dataset)),
        "registry": {
            "active_version": registry.get("active_version"),
            "active_artifact": registry.get("active_artifact"),
        },
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    EVALUATION_REPORT_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata


def main() -> None:
    metadata = train_model()
    print("Training complete.")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
