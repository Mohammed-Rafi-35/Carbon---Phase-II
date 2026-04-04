from __future__ import annotations

import time
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.auth.dependencies import verify_bearer_token
from app.config.settings import get_settings
from app.middleware.request_id import RequestIDMiddleware
from app.routes.ai_proxy import router as ai_proxy_router
from app.routes.analytics_proxy import router as analytics_proxy_router
from app.routes.claims_proxy import router as claims_proxy_router
from app.routes.fraud_proxy import router as fraud_proxy_router
from app.routes.identity_proxy import router as identity_proxy_router
from app.routes.notification_proxy import router as notification_proxy_router
from app.routes.payout_proxy import router as payout_proxy_router
from app.routes.policy_proxy import router as policy_proxy_router
from app.routes.trigger_proxy import router as trigger_proxy_router
from app.utils.responses import error_response


settings = get_settings()
RATE_LIMIT: dict[str, int] = {}
RATE_LIMIT_LOCK = Lock()
REQUEST_COUNTER = Counter("api_gateway_http_requests_total", "Total API requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("api_gateway_http_request_seconds", "Latency of API requests", ["method", "path"])


def _is_auth_exempt_path(path: str) -> bool:
	for exempt_path in settings.auth_exempt_paths:
		if not exempt_path:
			continue
		normalized = exempt_path.rstrip("/")
		if path == normalized or path.startswith(f"{normalized}/"):
			return True
	return False


def _rate_limit_key(client_ip: str) -> str:
	current_window = int(time.time() // 60)
	return f"{client_ip}:{current_window}"


def _is_rate_limited(client_ip: str) -> bool:
	key = _rate_limit_key(client_ip)
	current_window = int(time.time() // 60)
	with RATE_LIMIT_LOCK:
		stale_keys = []
		for counter_key in RATE_LIMIT:
			_, _, window_raw = counter_key.rpartition(":")
			try:
				window_value = int(window_raw)
			except ValueError:
				stale_keys.append(counter_key)
				continue
			if window_value < current_window - 1:
				stale_keys.append(counter_key)

		for stale_key in stale_keys:
			RATE_LIMIT.pop(stale_key, None)

		RATE_LIMIT[key] = RATE_LIMIT.get(key, 0) + 1
		return RATE_LIMIT[key] > settings.rate_limit_per_minute

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
	allow_origins=settings.cors_allow_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
	expose_headers=["X-Request-ID"],
)

if settings.enforce_https:
	app.add_middleware(HTTPSRedirectMiddleware)


@app.middleware("http")
async def gateway_control_middleware(request: Request, call_next):
	method = request.method
	path = request.url.path
	REQUEST_COUNTER.labels(method=method, path=path, status="received").inc()

	request_id = request.headers.get("X-Request-ID") or getattr(request.state, "request_id", None) or str(uuid4())
	request.state.request_id = request_id
	headers = {"X-Request-ID": request_id}

	content_length_header = request.headers.get("content-length")
	if content_length_header:
		try:
			content_length = int(content_length_header)
		except ValueError:
			return error_response(400, "INVALID_CONTENT_LENGTH", "Invalid Content-Length header.", headers=headers)
		if content_length > settings.max_request_body_bytes:
			return error_response(413, "REQUEST_TOO_LARGE", "Request body exceeds 1MB limit.", headers=headers)
	elif request.method in {"POST", "PUT", "PATCH"}:
		body = await request.body()
		if len(body) > settings.max_request_body_bytes:
			return error_response(413, "REQUEST_TOO_LARGE", "Request body exceeds 1MB limit.", headers=headers)

	client_ip = request.client.host if request.client else "unknown"
	if _is_rate_limited(client_ip):
		return error_response(429, "RATE_LIMIT_EXCEEDED", "Rate limit exceeded.", headers=headers)

	if request.method != "OPTIONS" and not _is_auth_exempt_path(request.url.path):
		authorization = request.headers.get("Authorization")
		try:
			request.state.token_payload = verify_bearer_token(authorization)
		except HTTPException as exc:
			detail = exc.detail if isinstance(exc.detail, dict) else {}
			code = str(detail.get("code", "UNAUTHORIZED"))
			message = str(detail.get("message", "Unauthorized"))
			REQUEST_COUNTER.labels(method=method, path=path, status=str(exc.status_code)).inc()
			return error_response(exc.status_code, code, message, headers=headers)

	with REQUEST_LATENCY.labels(method=method, path=path).time():
		response = await call_next(request)
	REQUEST_COUNTER.labels(method=method, path=path, status=str(response.status_code)).inc()
	return response


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


@app.get("/metrics")
def metrics() -> Response:
	return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(analytics_proxy_router)
app.include_router(identity_proxy_router)
app.include_router(policy_proxy_router)
app.include_router(claims_proxy_router)
app.include_router(fraud_proxy_router)
app.include_router(payout_proxy_router)
app.include_router(ai_proxy_router)
app.include_router(notification_proxy_router)
app.include_router(trigger_proxy_router)
