from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.routes.proxy_common import SUPPORTED_METHODS, proxy_request


router = APIRouter(tags=["trigger-proxy"])


@router.api_route("/api/v1/trigger", methods=SUPPORTED_METHODS)
async def proxy_trigger_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Trigger",
        base_url=settings.trigger_service_url,
        api_prefix=settings.trigger_api_prefix,
        resource_prefix="trigger",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/trigger/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_trigger_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Trigger",
        base_url=settings.trigger_service_url,
        api_prefix=settings.trigger_api_prefix,
        resource_prefix="trigger",
        path=path,
        request_id=request_id,
    )