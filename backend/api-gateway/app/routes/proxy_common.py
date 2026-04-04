from __future__ import annotations

import asyncio
import logging
import time
from threading import Lock
from urllib.parse import urlparse

import httpx
from fastapi import Request
from starlette.responses import Response

from app.config.settings import get_settings
from app.utils.responses import error_response


logger = logging.getLogger(__name__)

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
}

SENSITIVE_HEADERS = {
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-internal-token",
}

ALLOWED_HEADERS = {
    "authorization",
    "accept",
    "content-type",
    "x-request-id",
    "x-idempotency-key",
}

SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
CIRCUIT_STATE: dict[str, dict[str, float | int]] = {}
CIRCUIT_LOCK = Lock()


class CircuitOpenError(RuntimeError):
    pass


def _circuit_key(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url


def _is_circuit_open(key: str) -> bool:
    now = time.time()
    with CIRCUIT_LOCK:
        state = CIRCUIT_STATE.get(key)
        if not state:
            return False
        opened_until = float(state.get("opened_until", 0.0))
        if opened_until > now:
            return True
        if opened_until > 0:
            state["opened_until"] = 0.0
            state["failures"] = 0
    return False


def _record_failure(key: str) -> None:
    settings = get_settings()
    now = time.time()
    with CIRCUIT_LOCK:
        state = CIRCUIT_STATE.setdefault(key, {"failures": 0, "opened_until": 0.0})
        failures = int(state.get("failures", 0)) + 1
        state["failures"] = failures
        if failures >= settings.circuit_breaker_failure_threshold:
            state["opened_until"] = now + settings.circuit_breaker_open_seconds


def _record_success(key: str) -> None:
    with CIRCUIT_LOCK:
        CIRCUIT_STATE[key] = {"failures": 0, "opened_until": 0.0}


def build_target_url(*, base_url: str, api_prefix: str, resource_prefix: str = "", path: str = "") -> str:
    base = f"{base_url.rstrip('/')}{api_prefix.rstrip('/')}"
    if resource_prefix:
        base = f"{base}/{resource_prefix.strip('/')}"
    return base if not path else f"{base}/{path.lstrip('/')}"


def build_forward_headers(request: Request, request_id: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in request.headers.items():
        lower_key = key.lower()
        if lower_key in HOP_BY_HOP_HEADERS or lower_key in SENSITIVE_HEADERS:
            continue
        if lower_key in ALLOWED_HEADERS:
            headers[key] = value

    headers["X-Request-ID"] = request_id
    return headers


async def safe_request(
    *,
    method: str,
    url: str,
    params: list[tuple[str, str]],
    headers: dict[str, str],
    content: bytes | None,
) -> httpx.Response:
    settings = get_settings()
    last_error: Exception | None = None
    key = _circuit_key(url)

    if _is_circuit_open(key):
        raise CircuitOpenError(f"Circuit is open for upstream {key}")

    for attempt in range(settings.upstream_retry_attempts):
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    content=content,
                )
                _record_success(key)
                return response
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            last_error = exc
            if attempt + 1 < settings.upstream_retry_attempts:
                await asyncio.sleep(settings.upstream_retry_backoff_seconds)

    _record_failure(key)

    if isinstance(last_error, httpx.TimeoutException):
        raise last_error
    raise httpx.HTTPError("Service unavailable") from last_error


async def proxy_request(
    *,
    request: Request,
    service_name: str,
    base_url: str,
    api_prefix: str,
    request_id: str,
    resource_prefix: str = "",
    path: str = "",
) -> Response:
    target_url = build_target_url(
        base_url=base_url,
        api_prefix=api_prefix,
        resource_prefix=resource_prefix,
        path=path,
    )
    forward_headers = build_forward_headers(request, request_id)
    raw_body = await request.body()

    logger.info("[%s] [api-gateway] [proxy] forwarding %s %s -> %s", request_id, request.method, request.url.path, target_url)

    try:
        upstream_response = await safe_request(
            method=request.method,
            url=target_url,
            params=request.query_params.multi_items(),
            headers=forward_headers,
            content=raw_body if raw_body else None,
        )
    except CircuitOpenError:
        logger.warning("[%s] [api-gateway] [proxy] circuit open for %s", request_id, service_name)
        return error_response(
            503,
            "CIRCUIT_OPEN",
            f"{service_name} service circuit is open.",
            headers={"X-Request-ID": request_id},
        )
    except httpx.TimeoutException:
        logger.warning("[%s] [api-gateway] [proxy] timeout contacting %s", request_id, service_name)
        return error_response(
            504,
            "UPSTREAM_TIMEOUT",
            f"{service_name} service timed out.",
            headers={"X-Request-ID": request_id},
        )
    except httpx.HTTPError:
        logger.warning("[%s] [api-gateway] [proxy] upstream unavailable: %s", request_id, service_name)
        return error_response(
            502,
            "UPSTREAM_UNAVAILABLE",
            f"{service_name} service is unavailable.",
            headers={"X-Request-ID": request_id},
        )

    downstream_headers = {
        key: value for key, value in upstream_response.headers.items() if key.lower() not in HOP_BY_HOP_HEADERS
    }
    downstream_headers["X-Request-ID"] = request_id

    logger.info("[%s] [api-gateway] [proxy] completed %s -> %s", request_id, request.url.path, upstream_response.status_code)

    return Response(
        status_code=upstream_response.status_code,
        content=upstream_response.content,
        headers=downstream_headers,
    )
