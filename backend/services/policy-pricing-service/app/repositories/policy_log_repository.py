from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy import PolicyLog


class PolicyLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, policy_id: UUID, status: str, reason: str | None = None) -> PolicyLog:
        entry = PolicyLog(policy_id=policy_id, status=status, reason=reason)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_for_policy(self, policy_id: UUID) -> list[PolicyLog]:
        stmt = select(PolicyLog).where(PolicyLog.policy_id == policy_id).order_by(PolicyLog.timestamp.desc())
        return list(self.db.execute(stmt).scalars().all())