# Analytics Service

Production-ready FastAPI microservice for centralized administrative analytics across all backend services.

## Responsibilities

- Aggregate system events from Event Bus
- Generate KPIs (claims rate, payouts, risk distribution)
- Provide dashboard-ready admin APIs
- Provide historical and near-real-time time-series analytics
- Support UI visualization workloads through predictable response shapes

## API Base

- Base path: `/api/v1`
- Endpoints are admin/service scoped (not worker-facing)

## Required Headers

- `Authorization: Bearer <token>`
- `X-Request-ID: <uuid>`

## Endpoints

- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/zones`
- `GET /api/v1/analytics/timeseries`
- `GET /api/v1/analytics/health`

## Response Envelope

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

## Event Ingestion

The service consumes events from RabbitMQ exchange `devtrails.events` (topic) using `ANALYTICS_EVENT_ROUTING_KEY` (default `#`).

Supported event types:

- `DISRUPTION_DETECTED`
- `CLAIM_INITIATED`
- `CLAIM_APPROVED`
- `FRAUD_DETECTED`
- `PAYOUT_COMPLETED`
- `POLICY_CREATED`

## Data Model

- `analytics_events`: normalized event ledger with dedup key
- `analytics_metrics`: metric samples for fast time-series reads
- `aggregated_stats`: pre-aggregated counters for summary KPIs

## Environment Variables

Use `.env.example` as baseline.

Core:

- `DATABASE_URL`
- `RABBITMQ_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `AUTO_CREATE_TABLES`
- `ENABLE_EVENT_CONSUMER`

Caching:

- `CACHE_TTL_SECONDS`
- `DASHBOARD_CACHE_TTL_SECONDS`
- `ZONES_CACHE_TTL_SECONDS`
- `TIMESERIES_CACHE_TTL_SECONDS`

Queue tuning:

- `ANALYTICS_EVENT_QUEUE_NAME`
- `ANALYTICS_EVENT_ROUTING_KEY`
- `RETRY_LIMIT`
- `PREFETCH_COUNT`

## Local Setup

1. Install dependencies:

```shell
pip install -r requirements.txt
```

2. Configure environment:

```shell
copy .env.example .env
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
docker build -t devtrails/analytics-service:1.0.0 -t devtrails/analytics-service:latest .
```

Run:

```shell
docker run -d --name analytics_service -p 8011:8000 --env-file .env devtrails/analytics-service:1.0.0
```

## Testing

Run test suite:

```shell
pytest -q
```
