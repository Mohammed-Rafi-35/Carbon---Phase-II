from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import create_access_token, create_refresh_token, decode_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.revoked_token_repo = RevokedTokenRepository(db)

    def register_user(self, name: str, phone: str, email: str, password: str) -> tuple[UUID, str, str]:
        if self.user_repo.get_by_phone(phone):
            raise AppError("Phone already registered.", "PHONE_ALREADY_EXISTS", 409)
        if self.user_repo.get_by_email(email):
            raise AppError("Email already registered.", "EMAIL_ALREADY_EXISTS", 409)

        password_hash = hash_password(password)
        user = self.user_repo.create(name=name, phone=phone, email=email, password_hash=password_hash)
        access_token, _access_jti, _access_exp = create_access_token(str(user.id), role="worker")
        refresh_token, refresh_jti, refresh_expires = create_refresh_token(str(user.id), role="worker")
        self.refresh_token_repo.create(user_id=user.id, token_jti=refresh_jti, expires_at=refresh_expires)
        return user.id, access_token, refresh_token

    def login_user(self, phone: str, password: str) -> tuple[UUID, str, str]:
        user = self.user_repo.get_by_phone(phone)
        if not user or not verify_password(password, user.password_hash):
            raise AppError("Invalid phone or password.", "INVALID_CREDENTIALS", 401)

        access_token, _access_jti, _access_exp = create_access_token(str(user.id), role="worker")
        refresh_token, refresh_jti, refresh_expires = create_refresh_token(str(user.id), role="worker")
        self.refresh_token_repo.create(user_id=user.id, token_jti=refresh_jti, expires_at=refresh_expires)
        return user.id, access_token, refresh_token

    def refresh_session(self, refresh_token: str) -> tuple[UUID, str, str]:
        payload = decode_access_token(refresh_token)
        if payload.get("typ") != "refresh":
            raise AppError("Token is not a refresh token.", "INVALID_TOKEN", 401)

        token_jti = str(payload.get("jti") or "")
        if not token_jti:
            raise AppError("Token payload is invalid.", "INVALID_TOKEN", 401)

        row = self.refresh_token_repo.get_active(token_jti=token_jti)
        if row is None:
            raise AppError("Refresh token is invalid or revoked.", "INVALID_REFRESH_TOKEN", 401)

        now = datetime.now(tz=timezone.utc)
        if row.expires_at <= now:
            self.refresh_token_repo.revoke(row, revoked_at=now)
            raise AppError("Refresh token has expired.", "INVALID_REFRESH_TOKEN", 401)

        user = self.user_repo.get_by_id(row.user_id)
        if user is None:
            raise AppError("User not found for token.", "USER_NOT_FOUND", 404)

        self.refresh_token_repo.revoke(row, revoked_at=now)
        access_token, _access_jti, _access_exp = create_access_token(str(user.id), role="worker")
        new_refresh_token, new_refresh_jti, new_refresh_exp = create_refresh_token(str(user.id), role="worker")
        self.refresh_token_repo.create(user_id=user.id, token_jti=new_refresh_jti, expires_at=new_refresh_exp)
        return user.id, access_token, new_refresh_token

    def logout(self, refresh_token: str) -> None:
        payload = decode_access_token(refresh_token)
        token_jti = str(payload.get("jti") or "")
        if not token_jti:
            raise AppError("Token payload is invalid.", "INVALID_TOKEN", 401)

        row = self.refresh_token_repo.get_active(token_jti=token_jti)
        now = datetime.now(tz=timezone.utc)
        if row is not None:
            self.refresh_token_repo.revoke(row, revoked_at=now)

        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
        self.revoked_token_repo.create(token_jti=token_jti, token_type="refresh", expires_at=expires_at)

    def get_user_by_id(self, user_id: UUID) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AppError("User not found.", "USER_NOT_FOUND", 404)
        return user
