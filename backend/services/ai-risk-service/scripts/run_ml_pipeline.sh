#!/usr/bin/env bash
set -euo pipefail

SKIP_TRAIN="false"
OPEN_NOTEBOOK="false"

for arg in "$@"; do
  case "$arg" in
    --skip-train) SKIP_TRAIN="true" ;;
    --open-notebook) OPEN_NOTEBOOK="true" ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SERVICE_ROOT/../../.." && pwd)"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_EXE="$PROJECT_ROOT/.venv/bin/python"
elif [[ -x "$PROJECT_ROOT/.venv/Scripts/python.exe" ]]; then
  PYTHON_EXE="$PROJECT_ROOT/.venv/Scripts/python.exe"
else
  PYTHON_EXE="python"
fi

cd "$SERVICE_ROOT"

echo "Using Python: $PYTHON_EXE"
echo "Service root: $SERVICE_ROOT"

echo "Step 1/5: Generate synthetic data"
"$PYTHON_EXE" -m ml.src.data_generation

echo "Step 2/5: Build HITL feedback dataset"
"$PYTHON_EXE" -m ml.src.build_feedback_dataset

if [[ "$SKIP_TRAIN" == "false" ]]; then
  echo "Step 3/5: Train model"
  "$PYTHON_EXE" -m ml.src.train
else
  echo "Step 3/5: Skipped training"
fi

echo "Step 4/5: Evaluate model"
"$PYTHON_EXE" -m ml.src.evaluate

echo "Step 5/5: Generate visualization report"
"$PYTHON_EXE" -m ml.src.generate_visuals

if [[ "$OPEN_NOTEBOOK" == "true" ]]; then
  NOTEBOOK_PATH="$SERVICE_ROOT/ml/notebooks/model_evaluation.ipynb"
  echo "Opening notebook: $NOTEBOOK_PATH"
  jupyter notebook "$NOTEBOOK_PATH"
fi

echo "Done. Check ml/models/metadata.json, ml/models/evaluation_report.json, and ml/models/reports/."
