from __future__ import annotations

from uuid import uuid4

from fastapi import Header, HTTPException, Request


AUTH_HEADER_NAME = "Authorization"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
BEARER_PREFIX = "Bearer "


def require_bearer_token(authorization: str | None = Header(default=None, alias=AUTH_HEADER_NAME)) -> str:
    if not authorization or not authorization.startswith(BEARER_PREFIX):
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "A valid Bearer token is required."},
        )
    return authorization[len(BEARER_PREFIX) :].strip()


def get_or_create_request_id(
    request: Request,
    request_id: str | None = Header(default=None, alias=REQUEST_ID_HEADER_NAME),
) -> str:
    resolved_request_id = request_id or str(uuid4())
    request.state.request_id = resolved_request_id
    return resolved_request_id
