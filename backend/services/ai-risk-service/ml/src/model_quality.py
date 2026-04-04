from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(root_mean_squared_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def summarize_cv(cv_results: dict[str, np.ndarray]) -> dict[str, float]:
    mae_scores = -cv_results["test_mae"]
    rmse_scores = -cv_results["test_rmse"]
    r2_scores = cv_results["test_r2"]

    return {
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores)),
        "rmse_mean": float(np.mean(rmse_scores)),
        "rmse_std": float(np.std(rmse_scores)),
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
    }


def diagnose_fit(
    train_metrics: dict[str, float],
    test_metrics: dict[str, float],
    *,
    min_test_r2: float = 0.75,
    max_r2_gap: float = 0.08,
    max_rmse_ratio: float = 1.4,
) -> dict[str, float | str]:
    train_r2 = train_metrics["r2"]
    test_r2 = test_metrics["r2"]
    train_rmse = train_metrics["rmse"]
    test_rmse = test_metrics["rmse"]

    r2_gap = train_r2 - test_r2
    rmse_ratio = test_rmse / max(train_rmse, 1e-9)

    if test_r2 < min_test_r2 and train_r2 < min_test_r2:
        status = "underfitting"
        message = "Model complexity is too low for the data pattern."
    elif r2_gap > max_r2_gap or rmse_ratio > max_rmse_ratio:
        status = "overfitting"
        message = "Generalization gap is high; model complexity is likely too high."
    else:
        status = "balanced"
        message = "Train/test behavior is stable with low generalization gap."

    return {
        "status": status,
        "message": message,
        "r2_gap": float(r2_gap),
        "rmse_ratio": float(rmse_ratio),
    }
