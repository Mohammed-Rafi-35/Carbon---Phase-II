from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.routes.proxy_common import proxy_request


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics-proxy"])


@router.get("")
async def proxy_analytics_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Analytics",
        base_url=settings.analytics_service_url,
        api_prefix=settings.analytics_api_prefix,
        path="",
        request_id=request_id,
    )


@router.get("/{path:path}")
async def proxy_analytics_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Analytics",
        base_url=settings.analytics_service_url,
        api_prefix=settings.analytics_api_prefix,
        path=path,
        request_id=request_id,
    )
