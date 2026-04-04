from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import AppError


def hash_password(password: str) -> str:
	return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
	return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(
	subject: str,
	*,
	role: str,
	expires_delta_seconds: int | None = None,
) -> tuple[str, str, datetime]:
	settings = get_settings()
	exp_seconds = expires_delta_seconds or settings.jwt_expiry
	expire_at = datetime.now(tz=timezone.utc) + timedelta(seconds=exp_seconds)
	token_jti = uuid4().hex
	payload = {
		"sub": subject,
		"role": role,
		"iss": settings.jwt_issuer,
		"jti": token_jti,
		"typ": "access",
		"exp": expire_at,
	}
	return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), token_jti, expire_at


def create_refresh_token(subject: str, *, role: str) -> tuple[str, str, datetime]:
	settings = get_settings()
	expire_at = datetime.now(tz=timezone.utc) + timedelta(days=settings.refresh_token_expiry_days)
	token_jti = uuid4().hex
	payload = {
		"sub": subject,
		"role": role,
		"iss": settings.jwt_issuer,
		"jti": token_jti,
		"typ": "refresh",
		"exp": expire_at,
	}
	return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), token_jti, expire_at


def decode_access_token(token: str) -> dict:
	settings = get_settings()
	try:
		payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
		if payload.get("iss") != settings.jwt_issuer:
			raise AppError("Token issuer is invalid.", "INVALID_TOKEN", 401)
		return payload
	except jwt.ExpiredSignatureError as exc:
		raise AppError("Token has expired.", "TOKEN_EXPIRED", 401) from exc
	except jwt.InvalidTokenError as exc:
		raise AppError("Invalid authentication token.", "INVALID_TOKEN", 401) from exc

