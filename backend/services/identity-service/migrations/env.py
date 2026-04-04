from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, engine_from_config, pool, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.base import Base
from app.models import refresh_token, revoked_token, user, worker_profile  # noqa: F401


config = context.config
settings = get_settings()


def _resolve_migration_database_url() -> str:
    if settings.database_url.startswith("sqlite"):
        return settings.database_url

    probe_connect_args = {}
    if settings.database_url.startswith("postgresql"):
        probe_connect_args = {"connect_timeout": settings.database_connect_timeout_seconds}

    primary_engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=probe_connect_args)
    try:
        with primary_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return settings.database_url
    except SQLAlchemyError:
        raise
    finally:
        primary_engine.dispose()


config.set_main_option("sqlalchemy.url", _resolve_migration_database_url())

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
