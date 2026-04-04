# Identity & Worker Service

Production-ready FastAPI microservice for user authentication and worker profile lifecycle management.

## Features

- Secure registration and login with bcrypt + JWT
- Token validation endpoint for session checks
- Worker profile create/update and retrieval
- Standardized response and error formats
- SQLAlchemy ORM with Alembic migrations
- Dockerized deployment
- Unit, integration, and load test assets

## API Endpoints

Base path: /api/v1

- POST /auth/register
- POST /auth/login
- GET /auth/validate
- POST /workers/profile
- GET /workers/{user_id}

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

## Environment Variables

- DATABASE_URL
- JWT_SECRET
- JWT_EXPIRY
- JWT_ALGORITHM
- REDIS_URL (optional)
- POLICY_SERVICE_URL
- CLAIMS_SERVICE_URL
- ENFORCE_HTTPS
- AUTO_CREATE_TABLES

Use .env.example as baseline.

## Local Development

1. Install dependencies:

pip install -r requirements.txt

2. Configure environment:

copy .env.example .env

3. Run migrations:

alembic upgrade head

4. Start server:

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

OpenAPI docs:

- /docs
- /redoc

## Docker

Standard image and container naming:

- Image: `devtrails/identity-service:1.0.0`
- Container: `identity-service`

For Docker Hub publishing, replace `devtrails` with your Docker Hub username.

Build (versioned + latest tags):

docker build -t devtrails/identity-service:1.0.0 -t devtrails/identity-service:latest .

Run (host port 8005, container port 8000):

docker run -d --name identity-service --env-file .env -p 8005:8000 devtrails/identity-service:1.0.0

Health check:

curl http://localhost:8005/health

Push to Docker Hub:

docker login
docker push devtrails/identity-service:1.0.0
docker push devtrails/identity-service:latest

Pull and run on another machine:

docker pull devtrails/identity-service:1.0.0
docker run -d --name identity-service --env-file .env -p 8005:8000 devtrails/identity-service:1.0.0

Legacy local-only build/run:

docker build -t identity-service:latest .

Run:

docker run --env-file .env -p 8000:8000 identity-service:latest

## Tests

Run unit + integration tests:

pytest -q

Run load tests (Locust):

locust -f tests/performance/locustfile.py --host http://localhost:8000

## Troubleshooting

- Invalid token: verify JWT_SECRET consistency across environments.
- DB connection failures: validate DATABASE_URL and PostgreSQL availability. In development, if PostgreSQL is unavailable and ENABLE_DEV_SQLITE_FALLBACK=true, the service automatically falls back to DEV_SQLITE_FALLBACK_URL.
- Migration errors: ensure alembic.ini url or DATABASE_URL is valid.
- Slow API: check indexes on users.phone and users.email.

