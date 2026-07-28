"""
seed.py — populate the database with sample data

Creates two users (alice and bob) and three notes for manual testing.
Drops and recreates all tables on every run, so it is safe to re-run
against a development database but should never be run in production.

Usage (from the repo root):
    python -m backend.seed
"""
from backend.app import create_app, db
from backend.models import User, Note


def seed_data():
    app = create_app()
    with app.app_context():
        # Wipe existing data so the seed is idempotent across re-runs.
        db.drop_all()
        db.create_all()

        alice = User(username="alice")
        alice.set_password("secret123")
        bob = User(username="bob")
        bob.set_password("password456")
        db.session.add_all([alice, bob])
        db.session.commit()

        db.session.add_all(
            [
                Note(title="First note", content="Hello from Alice", user_id=alice.id),
                Note(title="Second note", content="Hello from Alice again", user_id=alice.id),
                Note(title="Bob note", content="Hello from Bob", user_id=bob.id),
            ]
        )
        db.session.commit()


if __name__ == "__main__":
    seed_data()
