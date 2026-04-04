from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.routes.proxy_common import SUPPORTED_METHODS, proxy_request


router = APIRouter(tags=["notification-proxy"])


@router.api_route("/api/v1/notify", methods=SUPPORTED_METHODS)
async def proxy_notify_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Notification",
        base_url=settings.notification_service_url,
        api_prefix=settings.notification_api_prefix,
        resource_prefix="notify",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/notify/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_notify_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Notification",
        base_url=settings.notification_service_url,
        api_prefix=settings.notification_api_prefix,
        resource_prefix="notify",
        path=path,
        request_id=request_id,
    )