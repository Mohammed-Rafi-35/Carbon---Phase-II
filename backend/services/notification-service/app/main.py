from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.api.v1.routes.notify import router as notify_router
from app.core.config import get_settings
from app.core.exceptions import (
	AppError,
	app_error_handler,
	http_exception_handler,
	unhandled_exception_handler,
	validation_exception_handler,
)
from app.db.base import Base
from app.db.session import engine
from app.events.bus_consumer import NotificationEventBusConsumer
from app.models import notification  # noqa: F401
from app.utils.logging import configure_logging
from app.utils.request_id import RequestIDMiddleware


settings = get_settings()
REQUEST_COUNTER = Counter("notification_http_requests_total", "Total API requests", ["method", "path"])
REQUEST_LATENCY = Histogram("notification_http_request_seconds", "Latency of API requests", ["method", "path"])
event_bus_consumer: NotificationEventBusConsumer | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
	global event_bus_consumer

	configure_logging()
	if settings.app_env == "test" and engine.url.get_backend_name() == "sqlite":
		Base.metadata.create_all(bind=engine)

	if settings.enable_event_bus_consumer and settings.app_env != "test":
		event_bus_consumer = NotificationEventBusConsumer()
		event_bus_consumer.start()
	yield

	if event_bus_consumer is not None:
		event_bus_consumer.stop()


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


app.include_router(notify_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
	return {"status": "healthy"}


@app.get("/metrics")
def metrics() -> Response:
	return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

