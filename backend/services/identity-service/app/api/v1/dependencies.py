from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.constants import AUTH_HEADER_NAME, BEARER_PREFIX, ERROR_INVALID_AUTH_HEADER
from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository


def get_authorization_header(authorization: str | None = Header(default=None, alias=AUTH_HEADER_NAME)) -> str:
	if not authorization or not authorization.startswith(BEARER_PREFIX):
		raise AppError(ERROR_INVALID_AUTH_HEADER, "UNAUTHORIZED", 401)
	return authorization[len(BEARER_PREFIX) :]


def get_current_user(token: str = Depends(get_authorization_header), db: Session = Depends(get_db)) -> User:
	payload = decode_access_token(token)
	token_jti = payload.get("jti")
	if not token_jti:
		raise AppError("Token payload is invalid.", "INVALID_TOKEN", 401)
	if RevokedTokenRepository(db).is_revoked(token_jti=str(token_jti)):
		raise AppError("Token has been revoked.", "TOKEN_REVOKED", 401)

	subject = payload.get("sub")
	if not subject:
		raise AppError("Token payload is invalid.", "INVALID_TOKEN", 401)
	try:
		user_id = UUID(subject)
	except ValueError as exc:
		raise AppError("Token payload is invalid.", "INVALID_TOKEN", 401) from exc

	user = UserRepository(db).get_by_id(user_id)
	if not user:
		raise AppError("User not found for token.", "USER_NOT_FOUND", 404)
	return user

