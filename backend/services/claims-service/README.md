# Claims & Decision Engine Service

Automated claims orchestration service for the event-driven insurance flow.

This service is the decision layer for claims. It validates policy eligibility, evaluates AI risk, checks fraud, makes approval/rejection decisions, and triggers payout processing.

## API Endpoints

- POST /api/v1/claims/auto
- GET /api/v1/claims/{user_id}
- GET /api/v1/claims/detail/{claim_id}
- POST /api/v1/claims/process

## Event Contracts

- Consumes `DISRUPTION_DETECTED` from `trigger.disruption_detected`
- Publishes `CLAIM_INITIATED` to `claim.initiated`
- Publishes `CLAIM_APPROVED` to `claim.approved`

## Claim Lifecycle

`initiated -> validated -> evaluated -> approved -> paid`

Reject path:

`initiated/validated/evaluated -> rejected`

Every transition is recorded in `claim_logs` for auditability.

## Environment Variables

- DATABASE_URL
- RABBITMQ_URL
- POLICY_SERVICE_URL
- AI_SERVICE_URL
- FRAUD_SERVICE_URL
- PAYOUT_SERVICE_URL
- RISK_REJECT_THRESHOLD
- DEFAULT_CLAIM_USERS_CSV
- DEFAULT_PAYOUT_AMOUNT
- JWT_SECRET

## Run Locally

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8013
```

## Production Notes

- Uses PostgreSQL via SQLAlchemy and Alembic migrations.
- Uses RabbitMQ for disruption event consumption and claim event publishing.
- Uses contract-compliant response envelope: `status`, `data`, `error`.
- Requires `Authorization` and `X-Request-ID` headers on secured endpoints.

## Docker

Build image:

```bash
docker build -t devtrails/claims-decision-engine:1.0.0 -t devtrails/claims-decision-engine:latest .
```

Run container:

```bash
docker run -d --name claims-decision-engine \
	-p 8013:8013 \
	-e PORT=8013 \
	-e DATABASE_URL=sqlite+pysqlite:///./claims.db \
	-e AUTO_CREATE_TABLES=true \
	-e ENABLE_EVENT_CONSUMER=false \
	-e RUN_MIGRATIONS=false \
	devtrails/claims-decision-engine:1.0.0
```

Smoke test (PowerShell):

```bash
powershell -ExecutionPolicy Bypass -File scripts/test_api_smoke.ps1 -BaseUrl http://localhost:8013
```

Smoke test (bash):

```bash
bash scripts/test_api_smoke.sh http://localhost:8013
```
