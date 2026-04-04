from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./trigger_service_test.db"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["ENABLE_MANUAL_TRIGGER"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = create_access_token(subject=str(uuid4()), role="worker", expires_hours=1)
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": str(uuid4()),
    }
