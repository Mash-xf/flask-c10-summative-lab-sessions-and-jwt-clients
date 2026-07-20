import pytest

from backend.app import create_app, db


@pytest.fixture()
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client


def register(client, username="alice", password="secret123"):
    return client.post(
        "/register",
        json={"username": username, "password": password},
    )


def login(client, username="alice", password="secret123"):
    return client.post(
        "/login",
        json={"username": username, "password": password},
    )


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login_flow(client):
    reg = register(client)
    assert reg.status_code == 201

    login_res = login(client)
    assert login_res.status_code == 200
    payload = login_res.get_json()
    assert payload["access_token"]
    assert payload["user"]["username"] == "alice"


def test_frontend_auth_routes_return_token_and_user(client):
    signup_res = client.post(
        "/signup",
        json={"username": "carol", "password": "secret123", "password_confirmation": "secret123"},
    )
    assert signup_res.status_code == 201
    signup_payload = signup_res.get_json()
    assert signup_payload["token"]
    assert signup_payload["user"]["username"] == "carol"

    me_res = client.get(
        "/me",
        headers={"Authorization": f"Bearer {signup_payload['token']}"},
    )
    assert me_res.status_code == 200
    assert me_res.get_json()["username"] == "carol"


def test_notes_are_scoped_to_the_authenticated_user(client):
    register(client, "alice", "secret123")
    register(client, "bob", "password456")

    alice_login = login(client, "alice", "secret123")
    bob_login = login(client, "bob", "password456")
    alice_token = alice_login.get_json()["access_token"]
    bob_token = bob_login.get_json()["access_token"]

    create_note = client.post(
        "/notes",
        json={"title": "Alpha", "content": "First note"},
        headers=auth_headers(alice_token),
    )
    assert create_note.status_code == 201

    list_res = client.get("/notes", headers=auth_headers(bob_token))
    assert list_res.status_code == 200
    items = list_res.get_json()["items"]
    assert items == []


def test_notes_support_crud_and_pagination(client):
    register(client, "alice", "secret123")
    login_res = login(client, "alice", "secret123")
    token = login_res.get_json()["access_token"]
    headers = auth_headers(token)

    for i in range(3):
        create_res = client.post(
            "/notes",
            json={"title": f"Note {i}", "content": f"Body {i}"},
            headers=headers,
        )
        assert create_res.status_code == 201

    page_one = client.get("/notes?page=1&per_page=2", headers=headers)
    assert page_one.status_code == 200
    payload = page_one.get_json()
    assert payload["page"] == 1
    assert payload["per_page"] == 2
    assert len(payload["items"]) == 2
    assert payload["total"] == 3

    created_id = payload["items"][0]["id"]
    update_res = client.patch(
        f"/notes/{created_id}",
        json={"content": "Updated"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.get_json()["content"] == "Updated"

    delete_res = client.delete(f"/notes/{created_id}", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.get_json()["message"] == "Note deleted"

    fetch_res = client.get(f"/notes/{created_id}", headers=headers)
    assert fetch_res.status_code == 404


def test_user_cannot_access_another_users_note(client):
    register(client, "alice", "secret123")
    register(client, "bob", "password456")

    alice_login = login(client, "alice", "secret123")
    bob_login = login(client, "bob", "password456")
    alice_token = alice_login.get_json()["access_token"]
    bob_token = bob_login.get_json()["access_token"]

    create_res = client.post(
        "/notes",
        json={"title": "Private", "content": "Secret"},
        headers=auth_headers(alice_token),
    )
    note_id = create_res.get_json()["id"]

    forbidden_get = client.get(f"/notes/{note_id}", headers=auth_headers(bob_token))
    assert forbidden_get.status_code == 404

    forbidden_patch = client.patch(
        f"/notes/{note_id}",
        json={"content": "Nope"},
        headers=auth_headers(bob_token),
    )
    assert forbidden_patch.status_code == 404

    forbidden_delete = client.delete(f"/notes/{note_id}", headers=auth_headers(bob_token))
    assert forbidden_delete.status_code == 404
