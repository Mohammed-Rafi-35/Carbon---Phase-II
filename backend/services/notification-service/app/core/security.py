from __future__ import annotations

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

