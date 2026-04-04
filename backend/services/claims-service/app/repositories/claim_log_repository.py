from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.claim_log import ClaimLog


class ClaimLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, claim_id: UUID, stage: str, message: str, details: dict | None = None) -> ClaimLog:
        row = ClaimLog(claim_id=claim_id, stage=stage, message=message, details=details)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_for_claim(self, claim_id: UUID) -> list[ClaimLog]:
        stmt = select(ClaimLog).where(ClaimLog.claim_id == claim_id).order_by(ClaimLog.created_at.asc())
        return list(self.db.execute(stmt).scalars().all())
