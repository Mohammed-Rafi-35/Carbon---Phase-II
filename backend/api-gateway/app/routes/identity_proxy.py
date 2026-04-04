from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.routes.proxy_common import SUPPORTED_METHODS, proxy_request


router = APIRouter(tags=["identity-proxy"])


@router.api_route("/api/v1/auth", methods=SUPPORTED_METHODS)
async def proxy_auth_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Identity",
        base_url=settings.identity_service_url,
        api_prefix=settings.identity_api_prefix,
        resource_prefix="auth",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/auth/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_auth_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Identity",
        base_url=settings.identity_service_url,
        api_prefix=settings.identity_api_prefix,
        resource_prefix="auth",
        path=path,
        request_id=request_id,
    )


@router.api_route("/api/v1/workers", methods=SUPPORTED_METHODS)
async def proxy_workers_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Identity",
        base_url=settings.identity_service_url,
        api_prefix=settings.identity_api_prefix,
        resource_prefix="workers",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/workers/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_workers_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Identity",
        base_url=settings.identity_service_url,
        api_prefix=settings.identity_api_prefix,
        resource_prefix="workers",
        path=path,
        request_id=request_id,
    )
