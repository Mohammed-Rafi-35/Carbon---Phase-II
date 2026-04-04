from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes.risk import router as risk_router
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
from app.models import prediction_log  # noqa: F401
from app.core.logging import configure_logging
from app.utils.request_id import RequestIDMiddleware


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
	configure_logging()
	if settings.app_env == "test" and engine.url.get_backend_name() == "sqlite":
		Base.metadata.create_all(bind=engine)
	yield


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


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "healthy"}


@app.get("/")
def root() -> JSONResponse:
	return JSONResponse(content={"service": settings.app_name, "status": "ready"})


app.include_router(risk_router, prefix=settings.api_v1_prefix)
