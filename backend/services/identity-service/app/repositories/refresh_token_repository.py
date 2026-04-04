from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: UUID, token_jti: str, expires_at: datetime) -> RefreshToken:
        row = RefreshToken(user_id=user_id, token_jti=token_jti, expires_at=expires_at)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_active(self, *, token_jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_jti == token_jti, RefreshToken.revoked_at.is_(None))
        return self.db.scalar(stmt)

    def revoke(self, row: RefreshToken, *, revoked_at: datetime) -> RefreshToken:
        row.revoked_at = revoked_at
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
