from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import Response

from app.api.v1.routes.analytics import router as analytics_router
from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.db.base import Base
from app.db.session import engine
from app.events.consumer import AnalyticsEventConsumer
from app.models import aggregated_stat, analytics_event, analytics_metric  # noqa: F401
from app.utils.logging import configure_logging
from app.utils.request_id import RequestIDMiddleware


settings = get_settings()
REQUEST_COUNTER = Counter("analytics_http_requests_total", "Total API requests", ["method", "path"])
REQUEST_LATENCY = Histogram("analytics_http_request_seconds", "Latency of API requests", ["method", "path"])
event_consumer: AnalyticsEventConsumer | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global event_consumer

    configure_logging()
    if settings.app_env == "test" and engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(bind=engine)

    if settings.enable_event_consumer and settings.app_env != "test":
        event_consumer = AnalyticsEventConsumer()
        event_consumer.start()
    yield

    if event_consumer is not None:
        event_consumer.stop()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.enforce_https:
    app.add_middleware(HTTPSRedirectMiddleware)


@app.middleware("http")
async def prometheus_middleware(request, call_next):
    method = request.method
    path = request.url.path
    REQUEST_COUNTER.labels(method=method, path=path).inc()
    with REQUEST_LATENCY.labels(method=method, path=path).time():
        response = await call_next(request)
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(analytics_router, prefix=settings.api_v1_prefix)
