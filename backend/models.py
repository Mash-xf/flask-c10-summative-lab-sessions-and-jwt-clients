"""
models.py — SQLAlchemy ORM models

Defines the two database tables used by the API:
  - User  : stores credentials; owns many Notes
  - Note  : the protected resource; belongs to one User
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """Registered user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Plain-text password is never stored; only the bcrypt hash.
    password_hash = db.Column(db.String(255), nullable=False)
    # Deleting a user cascades to all of their notes.
    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash *password* with bcrypt and store the result."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """Return True if *password* matches the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)


class Note(db.Model):
    """A note that belongs to a single user."""

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # Foreign key enforces ownership at the database level.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="notes")

    def to_dict(self):
        """Return a JSON-serialisable representation of this note."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
        }
