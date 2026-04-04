from __future__ import annotations

from collections import defaultdict, deque
from time import time
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import AUTH_HEADER_NAME, BEARER_PREFIX, ERROR_INVALID_AUTH_HEADER, REQUEST_ID_HEADER_NAME
from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db


rate_limit_state: dict[str, deque[float]] = defaultdict(deque)


def get_authorization_header(authorization: str | None = Header(default=None, alias=AUTH_HEADER_NAME)) -> str:
	if not authorization or not authorization.startswith(BEARER_PREFIX):
		raise AppError(ERROR_INVALID_AUTH_HEADER, "UNAUTHORIZED", 401)
	return authorization[len(BEARER_PREFIX) :]


def get_request_id(request_id: str | None = Header(default=None, alias=REQUEST_ID_HEADER_NAME)) -> str:
	if not request_id:
		raise AppError("X-Request-ID header is required.", "MISSING_REQUEST_ID", 400)
	return request_id


def get_token_payload(token: str = Depends(get_authorization_header)) -> dict:
	return decode_access_token(token)


def get_current_subject(payload: dict = Depends(get_token_payload)) -> UUID:
	subject = payload.get("sub")
	if not subject:
		raise AppError("Token payload is invalid.", "INVALID_TOKEN", 401)
	try:
		return UUID(subject)
	except ValueError as exc:
		raise AppError("Token payload is invalid.", "INVALID_TOKEN", 401) from exc


def require_roles(*allowed_roles: str):
	def _dependency(payload: dict = Depends(get_token_payload)) -> str:
		role = str(payload.get("role", "worker")).lower()
		if allowed_roles and role not in {r.lower() for r in allowed_roles}:
			raise AppError("Insufficient privileges.", "FORBIDDEN", 403)
		return role

	return _dependency


def get_rate_limiter_key(request: Request, subject: UUID = Depends(get_current_subject)) -> str:
	host = request.client.host if request.client else "unknown"
	return f"{subject}:{host}"


def enforce_rate_limit(key: str = Depends(get_rate_limiter_key)) -> None:
	settings = get_settings()
	now = time()
	bucket = rate_limit_state[key]
	while bucket and now - bucket[0] > 60:
		bucket.popleft()
	if len(bucket) >= settings.rate_limit_per_minute:
		raise AppError("Rate limit exceeded.", "RATE_LIMIT_EXCEEDED", 429)
	bucket.append(now)


def get_db_session(db: Session = Depends(get_db)) -> Session:
	return db

