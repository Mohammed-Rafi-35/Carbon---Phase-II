# Policy & Pricing Service

Production-grade FastAPI microservice for policy lifecycle management, premium computation, eligibility validation, and claim-facing policy checks.

## Features

- Weekly actuarial premium calculation with zone rates, stabilization factor, and GST
- Full policy lifecycle support with waiting-period activation and validation
- Deterministic eligibility checks for claims processing
- PostgreSQL persistence with Alembic migrations
- JWT authentication, role checks, and in-memory rate limiting
- REST integrations with Identity, Fraud, Claims, and AI Risk services
- RabbitMQ lifecycle event publishing
- Prometheus metrics endpoint and structured JSON logging

## API Endpoints

Base path: /api/v1

- POST /policy/create
- GET /policy/{user_id}
- POST /policy/validate
- POST /pricing/calculate

## Global Response Contract

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

## Core Business Rules

- Weekly Premium = IWI x Zone Rate x Stabilization Factor x Risk Multiplier
- Total Premium = Weekly Premium + GST (18%)
- Eligibility:
	- active_days >= 3
	- waiting period completed (48h default)
	- fraud flag absent
	- premium paid
- Coverage rates:
	- LR-1: 60%
	- MR-2: 70%
	- HR-3: 80%

## Environment Variables

- DATABASE_URL
- RABBITMQ_URL
- REDIS_URL
- JWT_SECRET
- JWT_ALGORITHM
- GST_RATE
- WAITING_PERIOD_HOURS
- RATE_LIMIT_PER_MINUTE
- ENFORCE_HTTPS
- AUTO_CREATE_TABLES
- IDENTITY_SERVICE_URL
- FRAUD_SERVICE_URL
- CLAIMS_SERVICE_URL
- AI_RISK_SERVICE_URL

Use `.env.example` as baseline.

For local runs with `backend/docker-compose.yml`, use:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/policy_pricing_db`

## Local Development

1. Install dependencies:

pip install -r requirements.txt

2. Configure environment:

copy .env.example .env

3. Run migrations:

alembic upgrade head

4. Start API:

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

5. Verify:

- Health: /health
- OpenAPI: /docs
- Metrics: /metrics

## Docker

Standard image and container naming:

- Image: devtrails/policy-pricing-service:1.0.0
- Container: policy_pricing_service

Build:

docker build -t devtrails/policy-pricing-service:1.0.0 -t devtrails/policy-pricing-service:latest .

Run:

docker run -d --name policy_pricing_service --env-file .env -p 8004:8000 devtrails/policy-pricing-service:1.0.0

## Testing

Run all tests:

pytest -q

Performance test:

locust -f tests/performance/locustfile.py --host=http://localhost:8004

Stress test:

locust -f tests/stress/locustfile.py --host=http://localhost:8004

## Monitoring and Logging

- Prometheus scrape endpoint: /metrics
- Dashboard backend: Grafana (infrastructure layer)
- Structured logging in JSON format

## CI/CD

GitHub Actions workflow:

- Builds Docker image
- Applies migrations
- Runs tests
- Provides deploy gate on main branch
