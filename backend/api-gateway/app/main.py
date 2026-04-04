from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.config.settings import get_settings
from app.middleware.request_id import RequestIDMiddleware
from app.routes.analytics_proxy import router as analytics_proxy_router
from app.routes.identity_proxy import router as identity_proxy_router
from app.utils.responses import error_response


settings = get_settings()

app = FastAPI(
	title=settings.app_name,
	version="1.0.0",
	docs_url="/docs",
	redoc_url="/redoc",
	openapi_url="/openapi.json",
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
	expose_headers=["X-Request-ID"],
)

if settings.enforce_https:
	app.add_middleware(HTTPSRedirectMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
	detail = exc.detail if isinstance(exc.detail, dict) else {}
	code = str(detail.get("code", "HTTP_ERROR"))
	message = str(detail.get("message", detail.get("detail", "Request failed.")))
	request_id = getattr(request.state, "request_id", None)
	headers = {"X-Request-ID": request_id} if request_id else None
	return error_response(exc.status_code, code, message, headers=headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, _: RequestValidationError):
	request_id = getattr(request.state, "request_id", None)
	headers = {"X-Request-ID": request_id} if request_id else None
	return error_response(400, "INVALID_QUERY", "Request validation failed.", headers=headers)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _: Exception):
	request_id = getattr(request.state, "request_id", None)
	headers = {"X-Request-ID": request_id} if request_id else None
	return error_response(500, "INTERNAL_SERVER_ERROR", "An unexpected error occurred.", headers=headers)


@app.get("/health")
def health() -> dict:
	return {
		"status": "success",
		"data": {"status": "healthy", "service": "api-gateway"},
		"error": None,
	}


app.include_router(analytics_proxy_router)
app.include_router(identity_proxy_router)
