#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time
from urllib.parse import urlparse

from sqlalchemy import create_engine, text


database_url = os.getenv("DATABASE_URL", "")
rabbitmq_url = os.getenv("RABBITMQ_URL", "").strip()
max_retries = int(os.getenv("DB_STARTUP_MAX_RETRIES", "20"))
retry_delay_seconds = float(os.getenv("DB_STARTUP_RETRY_DELAY_SECONDS", "2"))
db_connect_timeout = int(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "5"))

if not database_url:
    raise RuntimeError("DATABASE_URL is required")

connect_args = {}
if database_url.startswith("postgresql"):
    connect_args = {"connect_timeout": db_connect_timeout}

for attempt in range(1, max_retries + 1):
    try:
        engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection established")
        break
    except Exception as exc:  # noqa: BLE001
        if attempt == max_retries:
            raise RuntimeError(f"Database is not reachable after {max_retries} attempts: {exc}") from exc
        print(f"Waiting for database ({attempt}/{max_retries}): {exc}")
        time.sleep(retry_delay_seconds)

if rabbitmq_url:
    parsed = urlparse(rabbitmq_url)
    host = parsed.hostname
    port = parsed.port or 5672
    if not host:
        raise RuntimeError("RABBITMQ_URL is set but host could not be resolved")

    for attempt in range(1, max_retries + 1):
        sock = socket.socket()
        sock.settimeout(2)
        try:
            sock.connect((host, port))
            print("RabbitMQ connection established")
            break
        except OSError as exc:
            if attempt == max_retries:
                raise RuntimeError(
                    f"RabbitMQ is not reachable after {max_retries} attempts at {host}:{port}: {exc}"
                ) from exc
            print(f"Waiting for RabbitMQ ({attempt}/{max_retries}) at {host}:{port}: {exc}")
            time.sleep(retry_delay_seconds)
        finally:
            sock.close()
PY

echo "Applying migrations"
alembic upgrade head

echo "Starting Analytics Service"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
