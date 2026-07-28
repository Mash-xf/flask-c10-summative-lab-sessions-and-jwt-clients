import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restful import Api

from backend.config import Config
from backend.models import db, bcrypt  # noqa: F401 — re-exported for tests
from backend.routes import register_resources


jwt = JWTManager()

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def create_app(test_config=None):
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


app = create_app()
