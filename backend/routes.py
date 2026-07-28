from flask import jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_restful import Resource

from backend.models import User, Note, db


class RegisterResource(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")
        password_confirmation = data.get("password_confirmation", "")

        if not username or not password:
            return {"errors": ["username and password are required"]}, 400

        if password != password_confirmation and password_confirmation:
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
                "token": token,
                "user": {"id": user.id, "username": user.username},
            },
            201,
        )


class LoginResource(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return {"errors": ["invalid credentials"]}, 401

        token = create_access_token(identity=str(user.id))
        return {"access_token": token, "token": token, "user": {"id": user.id, "username": user.username}}, 200


class MeResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = int(get_jwt_identity())
        user = db.session.get(User, current_user_id)
        if not user:
            return {"error": "user not found"}, 404
        return {"id": user.id, "username": user.username}, 200


class NoteListResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = int(get_jwt_identity())
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

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
    @jwt_required()
    def get(self, note_id):
        current_user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        if not note:
            return {"error": "note not found"}, 404
        return note.to_dict(), 200

    @jwt_required()
    def patch(self, note_id):
        current_user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
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
        current_user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        if not note:
            return {"error": "note not found"}, 404

        db.session.delete(note)
        db.session.commit()
        return {"message": "Note deleted"}, 200


def register_resources(api):
    api.add_resource(RegisterResource, "/register", "/signup")
    api.add_resource(LoginResource, "/login")
    api.add_resource(MeResource, "/me")
    api.add_resource(NoteListResource, "/notes")
    api.add_resource(NoteResource, "/notes/<int:note_id>")
