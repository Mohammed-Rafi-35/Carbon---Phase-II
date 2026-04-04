#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8003}"
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

echo "Starting AI Risk Service"
echo "Service root: $SERVICE_ROOT"
echo "Python executable: $PYTHON_EXE"
echo "Port: $PORT"

cd "$SERVICE_ROOT"
"$PYTHON_EXE" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
