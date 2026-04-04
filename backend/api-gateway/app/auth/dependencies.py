from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Header, HTTPException, Request
from jose import JWTError, jwt

from app.config.settings import get_settings


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


def verify_jwt_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={"verify_aud": False})
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token."},
        ) from exc


def verify_bearer_token(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith(BEARER_PREFIX):
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "A valid Bearer token is required."},
        )
    token = authorization[len(BEARER_PREFIX) :].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "A valid Bearer token is required."},
        )
    return verify_jwt_token(token)


def get_or_create_request_id(
    request: Request,
    request_id: str | None = Header(default=None, alias=REQUEST_ID_HEADER_NAME),
) -> str:
    resolved_request_id = request_id or str(uuid4())
    request.state.request_id = resolved_request_id
    return resolved_request_id
