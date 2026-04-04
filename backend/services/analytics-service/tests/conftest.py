from __future__ import annotations

import os
import platform
from datetime import datetime, timedelta, timezone

if os.name == "nt":
    platform.machine = lambda: os.environ.get("PROCESSOR_ARCHITECTURE", "AMD64")

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["ENABLE_EVENT_CONSUMER"] = "false"

from app.api.v1.dependencies import get_db_session  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402


get_settings.cache_clear()

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _token(role: str) -> str:
    return jwt.encode(
        {
            "sub": "analytics-test-subject",
            "role": role,
            "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
        },
        "test-secret",
        algorithm="HS256",
    )


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_token('admin')}",
        "X-Request-ID": "req-analytics-test-admin",
        "Content-Type": "application/json",
    }


@pytest.fixture
def service_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_token('service')}",
        "X-Request-ID": "req-analytics-test-service",
        "Content-Type": "application/json",
    }


@pytest.fixture
def worker_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_token('worker')}",
        "X-Request-ID": "req-analytics-test-worker",
        "Content-Type": "application/json",
    }


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
