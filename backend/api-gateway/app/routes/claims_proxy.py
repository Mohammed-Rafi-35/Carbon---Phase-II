from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.routes.proxy_common import SUPPORTED_METHODS, proxy_request


router = APIRouter(tags=["claims-proxy"])


@router.api_route("/api/v1/claims", methods=SUPPORTED_METHODS)
async def proxy_claims_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Claims",
        base_url=settings.claims_service_url,
        api_prefix=settings.claims_api_prefix,
        resource_prefix="claims",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/claims/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_claims_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Claims",
        base_url=settings.claims_service_url,
        api_prefix=settings.claims_api_prefix,
        resource_prefix="claims",
        path=path,
        request_id=request_id,
    )
