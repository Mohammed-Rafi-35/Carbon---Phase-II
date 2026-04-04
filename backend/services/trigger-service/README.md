# Trigger Service

Production-grade FastAPI microservice for disruption detection and event triggering.

## Responsibilities

- Poll external weather, traffic, and platform sources.
- Detect threshold breaches and generate disruption events.
- Persist active disruptions in the service-owned database.
- Publish `DISRUPTION_DETECTED` events to RabbitMQ.
- Expose manual and monitoring APIs under `/api/v1/trigger`.

## API Endpoints

- `POST /api/v1/trigger/mock`
- `GET /api/v1/trigger/active`
- `POST /api/v1/trigger/stop`

## Request/Response Standards

- `Authorization: Bearer <token>` required.
- `X-Request-ID: <uuid>` required.
- Standard envelope:

```json
{
	"status": "success",
	"data": {},
	"error": null
}
```

Error envelope:

```json
{
	"status": "error",
	"data": null,
	"error": {
		"code": "ERROR_CODE",
		"message": "Description"
	}
}
```

## Event Contract

Published message:

```json
{
	"event": "DISRUPTION_DETECTED",
	"event_id": "uuid",
	"zone": "string",
	"type": "weather|traffic|platform",
	"severity": "LOW|MEDIUM|HIGH",
	"timestamp": "ISO-8601"
}
```

## Environment Variables

- `DATABASE_URL`
- `RABBITMQ_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `POLL_INTERVAL_SECONDS`
- `POLL_ZONES_CSV`
- `WEATHER_API_URL`
- `TRAFFIC_API_URL`
- `PLATFORM_API_URL`
- `THRESHOLD_RAIN`
- `THRESHOLD_TRAFFIC`
- `THRESHOLD_PLATFORM_OUTAGE`
- `ENABLE_SCHEDULER`

## Local Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Testing

```bash
pytest -q
```

## Docker (Conflict-Free)

This service includes a dedicated `docker-compose.yml` with ports that avoid clashes with existing services.

- Trigger API: `8008 -> 8000`
- Trigger Postgres: `5439 -> 5432`
- Trigger RabbitMQ: `5679 -> 5672`
- Trigger RabbitMQ Management: `15679 -> 15672`

### Build and Start

```bash
docker compose up -d --build
```

### Check Container Health

```bash
docker compose ps
docker inspect --format='{{json .State.Health}}' trigger-service
```

### Verify API Health Endpoint

```bash
curl http://localhost:8008/health
```

### Stop

```bash
docker compose down
```
