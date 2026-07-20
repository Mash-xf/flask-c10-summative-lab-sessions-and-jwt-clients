import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context

from backend.models import db
from backend.app import create_app

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

app = create_app()
app.app_context().push()

target_metadata = db.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = current_app.extensions["sqlalchemy"].db.get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
