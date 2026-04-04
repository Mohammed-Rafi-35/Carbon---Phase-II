from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


def _create_engine(database_url: str):
	connect_args = {}
	if database_url.startswith("sqlite"):
		connect_args = {"check_same_thread": False}
	elif database_url.startswith("postgresql"):
		connect_args = {"connect_timeout": settings.database_connect_timeout_seconds}

	return create_engine(
		database_url,
		pool_pre_ping=True,
		connect_args=connect_args,
	)


engine = _create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

