# Payout Service

Production-ready FastAPI microservice for payout processing, transaction traceability, idempotency-safe disbursement, and ledger auditability.

## Features

- Process payouts for approved claims using a gateway abstraction
- Enforce idempotency with `Idempotency-Key`
- Prevent duplicate payouts per claim
- Persist payout lifecycle (`pending`, `completed`, `failed`)
- Maintain user ledger entries with running balance
- Retry failed payouts through controlled API
- JWT-authenticated endpoints with role checks
- Standard response and error envelope compliance
- Structured JSON logging and Prometheus metrics

## API Base

- Base path: `/api/v1`

## Required Headers

- `Authorization: Bearer <token>`
- `Content-Type: application/json`
- `X-Request-ID: <uuid>`

Additional header for payout processing:

- `Idempotency-Key: <unique-string>`

## Endpoints

- `POST /api/v1/payout/process`
- `GET /api/v1/payout/{user_id}`
- `POST /api/v1/payout/retry`

### Response Envelope

Success:

{
	"status": "success",
	"data": {},
	"error": null
}

Error:

{
	"status": "error",
	"data": null,
	"error": {
		"code": "ERROR_CODE",
		"message": "Description"
	}
}

## Database Schema

Primary tables:

- `payouts`
- `ledger`

The service also persists `idempotency_key` in `payouts` to guarantee replay safety.

## Environment Variables

Use `.env.example` as baseline.

Environment-specific templates included:

- `.env.development`
- `.env.staging`
- `.env.production`

Core:

- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `RATE_LIMIT_PER_MINUTE`
- `ENFORCE_HTTPS`
- `AUTO_CREATE_TABLES`

Payment integration:

- `PAYMENT_PROVIDER` (`mock`, `razorpay`, `stripe`, etc.)
- `PAYMENT_GATEWAY_API_KEY`
- `PAYMENT_GATEWAY_SECRET`
- `MOCK_GATEWAY_FORCE_FAILURE`

Events (optional):

- `ENABLE_EVENT_PUBLISH`
- `RABBITMQ_URL`
- `PAYOUT_COMPLETED_EVENT_ROUTING_KEY`
- `PAYOUT_FAILED_EVENT_ROUTING_KEY`

## Local Setup

1. Install dependencies:

```shell
pip install -r requirements.txt
```

2. Configure environment:

```shell
copy .env.example .env
```

For environment-specific setup:

```shell
copy .env.development .env
```

or

```shell
copy .env.staging .env
```

or

```shell
copy .env.production .env
```

3. Run DB migrations:

```shell
alembic upgrade head
```

4. Start service:

```shell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Verify:

- Health: `/health`
- OpenAPI: `/docs`
- Metrics: `/metrics`

## Docker

Build:

```shell
docker build -t devtrails/payout-service:1.0.0 -t devtrails/payout-service:latest .
```

Run:

```shell
docker run -d --name payout_service -p 8007:8000 --env-file .env devtrails/payout-service:1.0.0
```

## CI/CD

Workflow: `.github/workflows/payout-service-ci.yml`

Stages:

- `test`: installs dependencies and runs `pytest`
- `build`: builds Docker image
- `deploy`: deployment placeholder for main branch

## Testing

Run test suite:

```shell
pytest -q
```

Performance test:

```shell
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

Stress test:

```shell
locust -f tests/stress/locustfile.py --host=http://localhost:8000
```

## Troubleshooting

- `401 INVALID_TOKEN`: verify JWT secret/algorithm and token expiration
- `400 MISSING_IDEMPOTENCY_KEY`: include `Idempotency-Key` for `/payout/process`
- `409 DUPLICATE_PAYOUT`: payout already exists for the same `claim_id`
- `500 PAYOUT_FAILED`: gateway failed or simulated failure enabled
- DB connectivity issues: verify `DATABASE_URL` and run `alembic upgrade head`

## Versioning

- API version: `/api/v1/`
- Recommended release strategy: semantic versioning (`MAJOR.MINOR.PATCH`)
