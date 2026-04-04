from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings
from app.core.exceptions import AppError


def decode_access_token(token: str) -> dict:
	settings = get_settings()
	try:
		return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
	except jwt.ExpiredSignatureError as exc:
		raise AppError("Token has expired.", "TOKEN_EXPIRED", 401) from exc
	except jwt.InvalidTokenError as exc:
		raise AppError("Invalid authentication token.", "INVALID_TOKEN", 401) from exc


def create_access_token(subject: str, role: str = "worker", expires_hours: int = 1) -> str:
	settings = get_settings()
	payload = {
		"sub": subject,
		"role": role,
		"exp": datetime.now(tz=timezone.utc) + timedelta(hours=expires_hours),
	}
	return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
