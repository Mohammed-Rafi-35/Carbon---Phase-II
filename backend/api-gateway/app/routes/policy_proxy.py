from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.routes.proxy_common import SUPPORTED_METHODS, proxy_request


router = APIRouter(tags=["policy-proxy"])


@router.api_route("/api/v1/policy", methods=SUPPORTED_METHODS)
async def proxy_policy_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Policy",
        base_url=settings.policy_service_url,
        api_prefix=settings.policy_api_prefix,
        resource_prefix="policy",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/policy/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_policy_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Policy",
        base_url=settings.policy_service_url,
        api_prefix=settings.policy_api_prefix,
        resource_prefix="policy",
        path=path,
        request_id=request_id,
    )


@router.api_route("/api/v1/pricing", methods=SUPPORTED_METHODS)
async def proxy_pricing_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Policy",
        base_url=settings.policy_service_url,
        api_prefix=settings.policy_api_prefix,
        resource_prefix="pricing",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/pricing/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_pricing_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Policy",
        base_url=settings.policy_service_url,
        api_prefix=settings.policy_api_prefix,
        resource_prefix="pricing",
        path=path,
        request_id=request_id,
    )
