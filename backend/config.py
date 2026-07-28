"""
config.py — application configuration

All sensitive values are read from environment variables so that secrets
are never hard-coded in source control. The fallback values are safe for
local development only and must be overridden in production.
"""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Used by Flask's session signing and CSRF protection.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Defaults to a local SQLite file; override with a real DB URL in production.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Must be at least 32 bytes for HS256; override in production.
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-jwt-key-change-me-32b")
