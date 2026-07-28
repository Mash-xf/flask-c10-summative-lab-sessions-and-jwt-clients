"""
conftest.py — pytest fixtures and shared test helpers

The `client` fixture spins up an isolated in-memory SQLite database for
every test, so tests never touch the development database and can run in
any order without side-effects.

Helper functions (register, login, auth_headers, get_token) are plain
functions — not fixtures — so they can be imported directly by test
modules and called with different arguments per test.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app import create_app, db  # noqa: E402


@pytest.fixture()
def client():
    """
    Yield a Flask test client backed by a fresh in-memory database.

    Tables are created before each test and the client is torn down
    automatically when the test finishes.
    """
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client


# ── shared helpers ────────────────────────────────────────────────────────────

def register(client, username="alice", password="secret123", password_confirmation=None):
    """POST /register and return the raw response."""
    payload = {"username": username, "password": password}
    if password_confirmation is not None:
        payload["password_confirmation"] = password_confirmation
    return client.post("/register", json=payload)


def login(client, username="alice", password="secret123"):
    """POST /login and return the raw response."""
    return client.post("/login", json={"username": username, "password": password})


def auth_headers(token):
    """Return an Authorization header dict for the given JWT."""
    return {"Authorization": f"Bearer {token}"}


def get_token(client, username="alice", password="secret123"):
    """Register, log in, and return the access token in one call."""
    register(client, username, password)
    res = login(client, username, password)
    return res.get_json()["access_token"]
