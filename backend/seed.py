from backend.app import create_app, db
from backend.models import User, Note


def seed_data():
    app = create_app()
    with app.app_context():
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
