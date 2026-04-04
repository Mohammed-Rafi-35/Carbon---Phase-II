from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

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
os.environ["WAITING_PERIOD_HOURS"] = "48"

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


@pytest.fixture
def worker_headers() -> dict:
    token = jwt.encode(
        {
            "sub": "16fd2706-8baf-433b-82eb-8c7fada847da",
            "role": "worker",
            "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
        },
        "test-secret",
        algorithm="HS256",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": "req-test-worker-001",
        "Content-Type": "application/json",
    }


@pytest.fixture
def service_headers() -> dict:
    token = jwt.encode(
        {
            "sub": "8beea6d7-c470-45ff-b0a0-4e025fdb0f2f",
            "role": "service",
            "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
        },
        "test-secret",
        algorithm="HS256",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": "req-test-service-001",
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
