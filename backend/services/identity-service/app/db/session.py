from __future__ import annotations

from collections.abc import Generator
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)



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


def _build_engine():
	primary_engine = _create_engine(settings.database_url)

	if settings.database_url.startswith("sqlite"):
		return primary_engine

	try:
		with primary_engine.connect() as connection:
			connection.execute(text("SELECT 1"))
		return primary_engine
	except SQLAlchemyError as exc:
		if settings.app_env == "development" and settings.enable_dev_sqlite_fallback:
			logger.warning(
				"Primary database is unavailable. Falling back to development SQLite at %s. Error: %s",
				settings.dev_sqlite_fallback_url,
				exc,
			)
			return _create_engine(settings.dev_sqlite_fallback_url)
		raise


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

