"""
app.py — application factory

Creates and configures the Flask app, registers all extensions,
and wires up the REST API routes.
"""
import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restful import Api

from backend.config import Config
from backend.models import db, bcrypt  # noqa: F401 — re-exported so tests can import db from here
from backend.routes import register_resources


jwt = JWTManager()

# Absolute path to the migrations folder so `flask db` works from any cwd.
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def create_app(test_config=None):
    """
    Application factory.

    Args:
        test_config (dict, optional): Config overrides used by the test suite
            (e.g. in-memory SQLite URI, TESTING=True).

    Returns:
        Flask: Fully configured application instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    Migrate(app, db, directory=MIGRATIONS_DIR)

    api = Api(app)
    register_resources(api)

    return app


# Module-level app instance used by `flask run` and the migration CLI.
app = create_app()
