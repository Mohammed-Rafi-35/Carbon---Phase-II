#!/bin/sh
set -e

python - <<'PY'
import os
import time

from sqlalchemy import create_engine, text


database_url = os.getenv("DATABASE_URL", "").strip()
max_retries = int(os.getenv("STARTUP_MAX_RETRIES", "30"))
retry_base_seconds = float(os.getenv("STARTUP_RETRY_BASE_SECONDS", "1"))
retry_max_seconds = float(os.getenv("STARTUP_RETRY_MAX_SECONDS", "8"))
db_connect_timeout = int(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "5"))

if not database_url:
    raise RuntimeError("DATABASE_URL is required")


def backoff_delay(attempt: int) -> float:
    return min(retry_max_seconds, retry_base_seconds * (2 ** (attempt - 1)))


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
        sleep_seconds = backoff_delay(attempt)
        print(f"Waiting for database ({attempt}/{max_retries}) in {sleep_seconds:.1f}s: {exc}")
        time.sleep(sleep_seconds)
PY

echo "Applying migrations"
alembic upgrade head

echo "Starting Identity Service"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
