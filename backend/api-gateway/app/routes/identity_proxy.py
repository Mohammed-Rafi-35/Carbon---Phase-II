from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.utils.responses import error_response


router = APIRouter(tags=["identity-proxy"])

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

SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


def _build_forward_headers(request: Request, request_id: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in request.headers.items():
        lower_key = key.lower()
        if lower_key in HOP_BY_HOP_HEADERS:
            continue
        if lower_key in {"authorization", "accept", "content-type"} or lower_key.startswith("x-"):
            headers[key] = value

    headers["X-Request-ID"] = request_id
    return headers


def _build_target_url(resource_prefix: str, path: str) -> str:
    settings = get_settings()
    base_url = f"{settings.identity_service_url.rstrip('/')}{settings.identity_api_prefix.rstrip('/')}"
    resource_url = f"{base_url}/{resource_prefix.strip('/')}"
    return resource_url if not path else f"{resource_url}/{path.lstrip('/')}"


async def _proxy_request(request: Request, resource_prefix: str, path: str, request_id: str) -> Response:
    settings = get_settings()
    target_url = _build_target_url(resource_prefix=resource_prefix, path=path)
    forward_headers = _build_forward_headers(request, request_id)
    raw_body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            upstream_response = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params.multi_items(),
                headers=forward_headers,
                content=raw_body if raw_body else None,
            )
    except httpx.TimeoutException:
        return error_response(504, "UPSTREAM_TIMEOUT", "Identity service timed out.", headers={"X-Request-ID": request_id})
    except httpx.HTTPError:
        return error_response(502, "UPSTREAM_UNAVAILABLE", "Identity service is unavailable.", headers={"X-Request-ID": request_id})

    downstream_headers = {
        key: value for key, value in upstream_response.headers.items() if key.lower() not in HOP_BY_HOP_HEADERS
    }
    downstream_headers["X-Request-ID"] = request_id

    return Response(
        status_code=upstream_response.status_code,
        content=upstream_response.content,
        headers=downstream_headers,
    )


@router.api_route("/api/v1/auth", methods=SUPPORTED_METHODS)
async def proxy_auth_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    return await _proxy_request(request=request, resource_prefix="auth", path="", request_id=request_id)


@router.api_route("/api/v1/auth/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_auth_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    return await _proxy_request(request=request, resource_prefix="auth", path=path, request_id=request_id)


@router.api_route("/api/v1/workers", methods=SUPPORTED_METHODS)
async def proxy_workers_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    return await _proxy_request(request=request, resource_prefix="workers", path="", request_id=request_id)


@router.api_route("/api/v1/workers/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_workers_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    return await _proxy_request(request=request, resource_prefix="workers", path=path, request_id=request_id)
