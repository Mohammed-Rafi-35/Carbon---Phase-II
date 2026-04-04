# Fraud Detection Service

Production-grade FastAPI microservice for fraud scoring, duplicate-pattern detection, audit logging, and event-driven fraud intelligence in the claims workflow.

## Responsibilities

- Evaluate claim fraud risk using deterministic rules.
- Enrich scoring with optional external signals (Identity and AI Risk).
- Persist immutable fraud decision logs.
- Support admin manual override with role guard.
- Consume claim initiation events and publish fraud detection events.

## API Base

- Base path: /api/v1

## Required Headers

- Authorization: Bearer <token>
- X-Request-ID: <uuid>

## Endpoints

- POST /api/v1/fraud/check
- GET /api/v1/fraud/{claim_id}
- POST /api/v1/fraud/override

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

## Fraud Check Contract

Request:

{
	"claim_id": "uuid",
	"user_id": "uuid",
	"activity": {
		"gps_valid": true,
		"activity_score": 0.8,
		"device_consistency": true
	},
	"event": {
		"zone": "string",
		"type": "weather|traffic|platform",
		"severity": "LOW|MEDIUM|HIGH"
	}
}

Response data:

{
	"fraud_score": 0.2,
	"status": "PASS|FAIL",
	"reason": null
}

## Event Contracts

Consumes:

- CLAIM_INITIATED from claim.initiated

Publishes:

- FRAUD_DETECTED to fraud.detected

Published payload shape:

{
	"event_type": "FRAUD_DETECTED",
	"event_id": "uuid",
	"timestamp": "ISO-8601",
	"payload": {
		"claim_id": "uuid",
		"user_id": "uuid",
		"fraud_score": 0.87,
		"reason": "gps_invalid,duplicate_claim_pattern",
		"source": "api|event|override"
	}
}

## Environment Variables

Core:

- DATABASE_URL
- RABBITMQ_URL
- JWT_SECRET
- JWT_ALGORITHM
- RATE_LIMIT_PER_MINUTE
- FRAUD_FAIL_THRESHOLD
- MAX_DUPLICATE_CLAIMS

Event bus:

- FRAUD_EXCHANGE_NAME
- FRAUD_INBOUND_QUEUE_NAME
- FRAUD_INBOUND_ROUTING_KEY
- FRAUD_DETECTED_ROUTING_KEY
- ENABLE_EVENT_CONSUMER
- RETRY_LIMIT
- PREFETCH_COUNT

Integrations:

- IDENTITY_SERVICE_URL
- AI_RISK_SERVICE_URL
- INTEGRATION_TIMEOUT_SECONDS

Optional ML scoring:

- ENABLE_ML
- MODEL_PATH

Runtime:

- APP_ENV
- PORT
- AUTO_CREATE_TABLES

## Local Development

1. Install dependencies:

pip install -r requirements.txt

2. Configure environment:

copy .env.example .env

3. Start API:

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

4. Verify:

- Health: /health
- Metrics: /metrics
- OpenAPI: /docs

## Docker

Build:

docker build -t devtrails/fraud-service:1.0.0 -t devtrails/fraud-service:latest .

Run:

docker run -d --name fraud-service --env-file .env -p 8010:8000 devtrails/fraud-service:1.0.0

## Testing

Run all tests:

pytest -q

## Scaling Notes

- Service is stateless and horizontally scalable.
- Database and RabbitMQ are external dependencies.
- In-memory rate limiting is process-local and should be replaced by Redis for strict distributed limits in production.
