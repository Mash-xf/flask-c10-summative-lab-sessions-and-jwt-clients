"""
routes.py — Flask-RESTful resource classes and route registration

Auth endpoints  : /register  /signup  /login  /me
Notes endpoints : /notes  /notes/<id>

All notes endpoints require a valid JWT in the Authorization header:
    Authorization: Bearer <token>

Users can only read or modify their own notes. Accessing another user's
note returns 404 (rather than 403) to avoid leaking record existence.
"""
from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_restful import Resource

from backend.models import User, Note, db


class RegisterResource(Resource):
    """Handle new user registration at POST /register and POST /signup."""

    def post(self):
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")
        password_confirmation = data.get("password_confirmation", "")

        if not username or not password:
            return {"errors": ["username and password are required"]}, 400

        # Only validate confirmation when the client actually sends it
        # (the /signup frontend route always sends it; /register may not).
        if password_confirmation and password != password_confirmation:
            return {"errors": ["passwords do not match"]}, 400

        if User.query.filter_by(username=username).first():
            return {"errors": ["username already exists"]}, 409

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        return (
            {
                "message": "User created",
                # "token" is the key the React frontend reads on signup.
                "token": token,
                "user": {"id": user.id, "username": user.username},
            },
            201,
        )


class LoginResource(Resource):
    """Authenticate an existing user at POST /login."""

    def post(self):
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return {"errors": ["invalid credentials"]}, 401

        token = create_access_token(identity=str(user.id))
        return (
            {
                # "access_token" is the standard JWT key; "token" is the alias
                # the React frontend reads after login.
                "access_token": token,
                "token": token,
                "user": {"id": user.id, "username": user.username},
            },
            200,
        )


class MeResource(Resource):
    """Return the currently authenticated user at GET /me."""

    @jwt_required()
    def get(self):
        current_user_id = int(get_jwt_identity())
        user = db.session.get(User, current_user_id)
        if not user:
            return {"error": "user not found"}, 404
        return {"id": user.id, "username": user.username}, 200


class NoteListResource(Resource):
    """
    Collection endpoint for the authenticated user's notes.

    GET  /notes          — paginated list (query params: page, per_page)
    POST /notes          — create a new note
    """

    @jwt_required()
    def get(self):
        current_user_id = int(get_jwt_identity())

        # Clamp page and per_page to safe ranges.
        page = max(request.args.get("page", 1, type=int), 1)
        per_page = min(max(request.args.get("per_page", 10, type=int), 1), 100)

        pagination = (
            Note.query.filter_by(user_id=current_user_id)
            .order_by(Note.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "items": [note.to_dict() for note in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }, 200

    @jwt_required()
    def post(self):
        current_user_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()

        if not title or not content:
            return {"error": "title and content are required"}, 400

        note = Note(title=title, content=content, user_id=current_user_id)
        db.session.add(note)
        db.session.commit()
        return note.to_dict(), 201


class NoteResource(Resource):
    """
    Single-note endpoint for the authenticated user.

    GET    /notes/<id>   — fetch one note
    PATCH  /notes/<id>   — update title and/or content
    DELETE /notes/<id>   — delete the note
    """

    def _get_owned_note(self, note_id):
        """
        Return the note only if it exists and belongs to the current user.
        Returns None when the note is missing or owned by someone else,
        which causes the caller to respond with 404.
        """
        current_user_id = int(get_jwt_identity())
        return Note.query.filter_by(id=note_id, user_id=current_user_id).first()

    @jwt_required()
    def get(self, note_id):
        note = self._get_owned_note(note_id)
        if not note:
            return {"error": "note not found"}, 404
        return note.to_dict(), 200

    @jwt_required()
    def patch(self, note_id):
        note = self._get_owned_note(note_id)
        if not note:
            return {"error": "note not found"}, 404

        data = request.get_json(silent=True) or {}
        if "title" in data:
            note.title = data["title"].strip()
        if "content" in data:
            note.content = data["content"].strip()

        db.session.commit()
        return note.to_dict(), 200

    @jwt_required()
    def delete(self, note_id):
        note = self._get_owned_note(note_id)
        if not note:
            return {"error": "note not found"}, 404

        db.session.delete(note)
        db.session.commit()
        return {"message": "Note deleted"}, 200


def register_resources(api):
    """Bind all resource classes to their URL rules."""
    api.add_resource(RegisterResource, "/register", "/signup")
    api.add_resource(LoginResource, "/login")
    api.add_resource(MeResource, "/me")
    api.add_resource(NoteListResource, "/notes")
    api.add_resource(NoteResource, "/notes/<int:note_id>")
