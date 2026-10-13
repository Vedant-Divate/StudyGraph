"""Alembic environment: online upgrade + offline --sql rendering."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.models import Base

config = context.config

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.config_ini_section
    configuration = dict(config.get_section(section, {}))
    configuration["sqlalchemy.url"] = os.environ.get(
        "DATABASE_URL_SYNC",
        "postgresql+psycopg://studygraph:studygraph@localhost:5432/studygraph",
    )
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
