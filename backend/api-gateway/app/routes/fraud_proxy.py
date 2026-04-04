from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.auth.dependencies import get_or_create_request_id
from app.config.settings import get_settings
from app.routes.proxy_common import SUPPORTED_METHODS, proxy_request


router = APIRouter(tags=["fraud-proxy"])


@router.api_route("/api/v1/fraud", methods=SUPPORTED_METHODS)
async def proxy_fraud_root(
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Fraud",
        base_url=settings.fraud_service_url,
        api_prefix=settings.fraud_api_prefix,
        resource_prefix="fraud",
        path="",
        request_id=request_id,
    )


@router.api_route("/api/v1/fraud/{path:path}", methods=SUPPORTED_METHODS)
async def proxy_fraud_path(
    path: str,
    request: Request,
    request_id: str = Depends(get_or_create_request_id),
) -> Response:
    settings = get_settings()
    return await proxy_request(
        request=request,
        service_name="Fraud",
        base_url=settings.fraud_service_url,
        api_prefix=settings.fraud_api_prefix,
        resource_prefix="fraud",
        path=path,
        request_id=request_id,
    )
