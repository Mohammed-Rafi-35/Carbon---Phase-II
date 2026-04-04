from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.revoked_token import RevokedToken


class RevokedTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, token_jti: str, token_type: str, expires_at: datetime) -> RevokedToken:
        row = RevokedToken(token_jti=token_jti, token_type=token_type, expires_at=expires_at)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def is_revoked(self, *, token_jti: str) -> bool:
        stmt = select(RevokedToken.id).where(RevokedToken.token_jti == token_jti)
        return self.db.scalar(stmt) is not None
