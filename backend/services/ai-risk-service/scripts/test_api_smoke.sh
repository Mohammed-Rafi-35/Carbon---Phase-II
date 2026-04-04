#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8003}"
JWT_SECRET="${2:-change-me-in-production}"

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

TOKEN="$($PYTHON_EXE -c "from datetime import datetime, timedelta, timezone; import jwt; print(jwt.encode({'sub':'smoke-test','role':'service','exp': datetime.now(tz=timezone.utc)+timedelta(hours=2)}, '$JWT_SECRET', algorithm='HS256'))")"

echo "Testing AI Risk API at $BASE_URL"

EVALUATE_RESPONSE="$(curl -sS -X POST "$BASE_URL/api/v1/risk/evaluate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "MR-2",
    "metrics": {
      "disruption_freq": 0.30,
      "duration": 18,
      "traffic": 0.62,
      "order_drop": 0.20,
      "activity": 0.84,
      "claims": 0.15
    },
    "context": {
      "rolling_disruption_3h": 0.25,
      "traffic_last_hour": 0.56,
      "previous_risk_score": 0.41
    }
  }')"

echo "Evaluate response:"
echo "$EVALUATE_RESPONSE"

PREDICTION_ID="$(echo "$EVALUATE_RESPONSE" | $PYTHON_EXE -c 'import json,sys; payload=json.load(sys.stdin); print(payload.get("data",{}).get("prediction_id",""))')"

echo "Health response:"
curl -sS "$BASE_URL/api/v1/risk/health" -H "Authorization: Bearer $TOKEN"
echo

echo "Drift response:"
curl -sS "$BASE_URL/api/v1/risk/drift" -H "Authorization: Bearer $TOKEN"
echo

if [[ -n "$PREDICTION_ID" ]]; then
  echo "Submitting feedback for prediction_id=$PREDICTION_ID"
  curl -sS -X POST "$BASE_URL/api/v1/risk/feedback" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"prediction_id\":$PREDICTION_ID,\"actual_outcome\":0.22,\"corrected_label\":\"LOW\",\"review_notes\":\"Smoke test feedback entry\"}"
  echo
fi

echo "Feedback list response:"
curl -sS "$BASE_URL/api/v1/risk/feedback?status=pending&limit=5" -H "Authorization: Bearer $TOKEN"
echo

echo "Smoke test completed."
