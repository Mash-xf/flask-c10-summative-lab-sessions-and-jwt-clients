import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app import create_app, db  # noqa: E402


@pytest.fixture()
def client():
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
    payload = {"username": username, "password": password}
    if password_confirmation is not None:
        payload["password_confirmation"] = password_confirmation
    return client.post("/register", json=payload)


def login(client, username="alice", password="secret123"):
    return client.post("/login", json={"username": username, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def get_token(client, username="alice", password="secret123"):
    register(client, username, password)
    res = login(client, username, password)
    return res.get_json()["access_token"]
