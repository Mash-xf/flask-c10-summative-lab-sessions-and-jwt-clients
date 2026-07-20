import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import generate_password_hash, check_password_hash


basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
jwt = JWTManager()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="notes")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
        }


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'app.db')}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret"),
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/register", methods=["POST"])
    def register():
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "username and password are required"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "username already exists"}), 409

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User created", "user": {"id": user.id, "username": user.username}}), 201

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "invalid credentials"}), 401

        token = create_access_token(identity=user.id)
        return jsonify({"access_token": token, "user": {"id": user.id, "username": user.username}}), 200

    @app.route("/notes", methods=["GET"])
    @jwt_required()
    def list_notes():
        current_user_id = get_jwt_identity()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        pagination = (
            Note.query.filter_by(user_id=current_user_id)
            .order_by(Note.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return jsonify(
            {
                "items": [note.to_dict() for note in pagination.items],
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            }
        ), 200

    @app.route("/notes", methods=["POST"])
    @jwt_required()
    def create_note():
        current_user_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()

        if not title or not content:
            return jsonify({"error": "title and content are required"}), 400

        note = Note(title=title, content=content, user_id=current_user_id)
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201

    @app.route("/notes/<int:note_id>", methods=["GET"])
    @jwt_required()
    def get_note(note_id):
        current_user_id = get_jwt_identity()
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        if not note:
            return jsonify({"error": "note not found"}), 404
        return jsonify(note.to_dict()), 200

    @app.route("/notes/<int:note_id>", methods=["PATCH"])
    @jwt_required()
    def update_note(note_id):
        current_user_id = get_jwt_identity()
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        if not note:
            return jsonify({"error": "note not found"}), 404

        data = request.get_json(silent=True) or {}
        if "title" in data:
            note.title = data["title"].strip()
        if "content" in data:
            note.content = data["content"].strip()

        db.session.commit()
        return jsonify(note.to_dict()), 200

    @app.route("/notes/<int:note_id>", methods=["DELETE"])
    @jwt_required()
    def delete_note(note_id):
        current_user_id = get_jwt_identity()
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        if not note:
            return jsonify({"error": "note not found"}), 404

        db.session.delete(note)
        db.session.commit()
        return jsonify({"message": "Note deleted"}), 200

    return app


app = create_app()
