"""
migrations/env.py — Alembic migration environment

Loaded automatically by `flask db upgrade / migrate / downgrade`.
Connects Alembic to the Flask app's SQLAlchemy engine so that
migrations run against the same database the app uses.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app import create_app
from backend.models import db

# Alembic Config object — gives access to values in alembic.ini.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build a real Flask app so we can read its SQLALCHEMY_DATABASE_URI.
app = create_app()
target_metadata = db.metadata


def run_migrations_offline():
    """
    Run migrations without an active database connection.

    Useful for generating SQL scripts to review before applying.
    """
    url = app.config["SQLALCHEMY_DATABASE_URI"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations against a live database connection.

    Uses db.engine (Flask-SQLAlchemy 3.x API) inside an explicit
    app context so the engine is fully initialised before use.
    """
    with app.app_context():
        connectable = db.engine
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
