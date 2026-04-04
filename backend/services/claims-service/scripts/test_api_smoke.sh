#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8013}"
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

SERVICE_TOKEN="$($PYTHON_EXE -c "from datetime import datetime, timedelta, timezone; import jwt; print(jwt.encode({'sub':'8beea6d7-c470-45ff-b0a0-4e025fdb0f2f','role':'service','exp': datetime.now(tz=timezone.utc)+timedelta(hours=2)}, '$JWT_SECRET', algorithm='HS256'))")"
WORKER_TOKEN="$($PYTHON_EXE -c "from datetime import datetime, timedelta, timezone; import jwt; print(jwt.encode({'sub':'16fd2706-8baf-433b-82eb-8c7fada847da','role':'worker','exp': datetime.now(tz=timezone.utc)+timedelta(hours=2)}, '$JWT_SECRET', algorithm='HS256'))")"

echo "[1/5] Health check"
curl -sS "$BASE_URL/health"
echo

echo "[2/5] Auto create claim"
CREATE_RESPONSE="$(curl -sS -X POST "$BASE_URL/api/v1/claims/auto" \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H "X-Request-ID: req-claims-smoke-001" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"16fd2706-8baf-433b-82eb-8c7fada847da","event_id":"99999999-9999-9999-9999-999999999999"}')"
echo "$CREATE_RESPONSE"

CLAIM_ID="$(echo "$CREATE_RESPONSE" | $PYTHON_EXE -c 'import json,sys; print(json.load(sys.stdin).get("data",{}).get("claim_id",""))')"

echo "[3/5] Process claim"
curl -sS -X POST "$BASE_URL/api/v1/claims/process" \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H "X-Request-ID: req-claims-smoke-001" \
  -H "Content-Type: application/json" \
  -d "{\"claim_id\":\"$CLAIM_ID\"}"
echo

echo "[4/5] Fetch user claims"
curl -sS "$BASE_URL/api/v1/claims/16fd2706-8baf-433b-82eb-8c7fada847da" \
  -H "Authorization: Bearer $WORKER_TOKEN" \
  -H "X-Request-ID: req-claims-smoke-002"
echo

echo "[5/5] Fetch claim detail"
curl -sS "$BASE_URL/api/v1/claims/detail/$CLAIM_ID" \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H "X-Request-ID: req-claims-smoke-001"
echo

echo "Smoke test completed for claims and decision engine."
