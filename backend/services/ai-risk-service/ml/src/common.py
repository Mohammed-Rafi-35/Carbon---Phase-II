from __future__ import annotations

from pathlib import Path


ML_DIR = Path(__file__).resolve().parents[1]
SERVICE_ROOT = ML_DIR.parent
DATA_RAW_DIR = ML_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ML_DIR / "data" / "processed"
MODELS_DIR = ML_DIR / "models"
CONFIG_DIR = ML_DIR / "configs"
NOTEBOOKS_DIR = ML_DIR / "notebooks"

RAW_DATA_PATH = DATA_RAW_DIR / "synthetic_risk_data.csv"
PROCESSED_DATA_PATH = DATA_PROCESSED_DIR / "risk_data_processed.csv"
TRAIN_DATA_PATH = DATA_PROCESSED_DIR / "risk_data_train.csv"
TEST_DATA_PATH = DATA_PROCESSED_DIR / "risk_data_test.csv"
MODEL_BUNDLE_PATH = MODELS_DIR / "risk_model_v1.pkl"
METADATA_PATH = MODELS_DIR / "metadata.json"
EVALUATION_REPORT_PATH = MODELS_DIR / "evaluation_report.json"
MODEL_REGISTRY_PATH = MODELS_DIR / "model_registry.json"
FEEDBACK_DATASET_PATH = DATA_PROCESSED_DIR / "risk_feedback_labeled.csv"
DEFAULT_TRAINING_CONFIG_PATH = CONFIG_DIR / "training_config.yaml"


def ensure_dirs() -> None:
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
