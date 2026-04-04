# Notification Service

Production-grade FastAPI microservice for centralized outbound notifications across SMS, push, and in-app channels.

## Features

- Multi-channel notifications: SMS, PUSH, IN_APP
- Async queue-based processing with RabbitMQ + Celery workers
- Retry mechanism controlled by MAX_RETRIES
- Notification history/status tracking in PostgreSQL
- Template-based message rendering
- Bulk notifications through a single send API
- JWT protected APIs
- HTTPS enforcement option
- Rate limiting and request tracing with X-Request-ID
- Structured JSON logging with sensitive content masking
- OpenAPI docs at /docs

## API Endpoints

- POST /api/v1/notify/send
- GET /api/v1/notify/{user_id}
- POST /api/v1/notify/retry

All API responses follow:

{
	"status": "success",
	"data": {},
	"error": null
}

## Required Headers

- Authorization: Bearer <token>
- Content-Type: application/json
- X-Request-ID: <uuid>

## Environment Variables

- DATABASE_URL=postgresql+psycopg://...
- RABBITMQ_URL=amqp://...
- REDIS_URL=redis://... (optional backend/buffering)
- SMS_API_KEY=...
- PUSH_API_KEY=...
- MAX_RETRIES=3
- JWT_SECRET=...
- JWT_ALGORITHM=HS256
- ENFORCE_HTTPS=false

## Local Run

1. Install dependencies.
2. Run migrations.
3. Start API.
4. Start worker.

Commands:
``` shell
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
celery -A app.worker:celery_app worker --loglevel=info --concurrency=2
```

## Health Check Verification

curl http://localhost:8000/health

Expected:

{
	"status": "healthy"
}

## Docker

Standard image and container naming:

- Image: `devtrails/notification-service:1.0.0`
- API container: `notification-service`
- Worker container: `notification-service-worker`

For Docker Hub publishing, replace `devtrails` with your Docker Hub username.

Build (versioned + latest tags):

``` shell
docker build -t devtrails/notification-service:1.0.0 -t devtrails/notification-service:latest .
```

Run API container (host port 8006, container port 8000):

``` shell
docker run -d --name notification-service -p 8006:8000 --env-file .env devtrails/notification-service:1.0.0
```

Run worker container (same image, worker command override):

``` shell
docker run -d --name notification-service-worker --env-file .env devtrails/notification-service:1.0.0 celery -A app.worker:celery_app worker --loglevel=info --concurrency=2
```

Push to Docker Hub:

``` shell
docker login
docker push devtrails/notification-service:1.0.0
docker push devtrails/notification-service:latest
```

Pull and run on another machine:

``` shell
docker pull devtrails/notification-service:1.0.0
docker run -d --name notification-service -p 8006:8000 --env-file .env devtrails/notification-service:1.0.0
docker run -d --name notification-service-worker --env-file .env devtrails/notification-service:1.0.0 celery -A app.worker:celery_app worker --loglevel=info --concurrency=2
```

Build and run with separated API + worker containers:
``` shell
docker compose up --build

Detached mode:

docker compose up -d --build

Container status:

docker compose ps

Container health check:

curl http://localhost:8006/health
```
## Testing

- Unit tests: pytest
- Integration tests: mocked provider and event flow
- Performance tests: Locust scenario in tests/performance
- Stress tests: high-request Locust scenario in tests/stress

Run test suite:

pytest -q

Performance test:

locust -f tests/performance/locustfile.py --host=http://localhost:8006

Stress test:

locust -f tests/stress/locustfile.py --host=http://localhost:8006

## Monitoring Notes

Tracked metrics in service layer:

- Delivery success rate
- Retry count
- Queue length

## Troubleshooting

- Notifications not sent: verify RabbitMQ connection and worker health
- High retry count: validate SMS/PUSH API keys and provider availability
- Delayed delivery: increase worker replicas/concurrency
- Missing logs: verify JSON log pipeline configuration

## Roadmap

- Advanced template engine
- Multi-language templates
- Notification prioritization
- Real-time WebSocket notifications
- AI-assisted notification timing optimization

