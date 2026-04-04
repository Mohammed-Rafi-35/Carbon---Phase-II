from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response
import httpx

from app.auth.dependencies import get_or_create_request_id, require_bearer_token
from app.config.settings import get_settings
from app.utils.responses import error_response


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics-proxy"])

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


def _build_target_url(path: str) -> str:
    settings = get_settings()
    base_url = f"{settings.analytics_service_url.rstrip('/')}{settings.analytics_api_prefix}"
    return base_url if not path else f"{base_url}/{path.lstrip('/')}"


async def _proxy_request(request: Request, path: str, request_id: str) -> Response:
    settings = get_settings()
    target_url = _build_target_url(path)
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
        return error_response(504, "UPSTREAM_TIMEOUT", "Analytics service timed out.", headers={"X-Request-ID": request_id})
    except httpx.HTTPError:
        return error_response(502, "UPSTREAM_UNAVAILABLE", "Analytics service is unavailable.", headers={"X-Request-ID": request_id})

    downstream_headers = {
        key: value for key, value in upstream_response.headers.items() if key.lower() not in HOP_BY_HOP_HEADERS
    }
    downstream_headers["X-Request-ID"] = request_id

    return Response(
        status_code=upstream_response.status_code,
        content=upstream_response.content,
        headers=downstream_headers,
    )


@router.get("")
async def proxy_analytics_root(
    request: Request,
    _: str = Depends(require_bearer_token),
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    return await _proxy_request(request=request, path="", request_id=request_id)


@router.get("/{path:path}")
async def proxy_analytics_path(
    path: str,
    request: Request,
    _: str = Depends(require_bearer_token),
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    return await _proxy_request(request=request, path=path, request_id=request_id)
