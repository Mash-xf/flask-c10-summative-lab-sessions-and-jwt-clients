"""
Auth flow and API contract tests.

The `client` fixture is provided automatically by conftest.py.
Helper functions are imported explicitly below.
"""
from backend.tests.conftest import auth_headers, get_token, login, register


# ── Registration ──────────────────────────────────────────────────────────────

def test_register_returns_201_with_token_and_user(client):
    res = register(client)
    assert res.status_code == 201
    body = res.get_json()
    assert body["token"]
    assert body["user"]["username"] == "alice"


def test_register_missing_username_returns_400(client):
    res = client.post("/register", json={"password": "secret123"})
    assert res.status_code == 400
    assert res.get_json()["errors"]


def test_register_missing_password_returns_400(client):
    res = client.post("/register", json={"username": "alice"})
    assert res.status_code == 400
    assert res.get_json()["errors"]


def test_register_password_mismatch_returns_400(client):
    res = client.post(
        "/signup",
        json={
            "username": "alice",
            "password": "secret123",
            "password_confirmation": "wrong",
        },
    )
    assert res.status_code == 400
    assert "passwords do not match" in res.get_json()["errors"]


def test_register_duplicate_username_returns_409(client):
    register(client)
    res = register(client)
    assert res.status_code == 409
    assert res.get_json()["errors"]


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_returns_200_with_token_and_user(client):
    register(client)
    res = login(client)
    assert res.status_code == 200
    body = res.get_json()
    assert body["access_token"]
    assert body["token"]                      # frontend alias
    assert body["user"]["username"] == "alice"


def test_login_wrong_password_returns_401(client):
    register(client)
    res = login(client, password="wrongpassword")
    assert res.status_code == 401
    assert res.get_json()["errors"]


def test_login_unknown_user_returns_401(client):
    res = login(client, username="nobody")
    assert res.status_code == 401
    assert res.get_json()["errors"]


# ── /me ───────────────────────────────────────────────────────────────────────

def test_me_returns_current_user(client):
    token = get_token(client)
    res = client.get("/me", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.get_json()["username"] == "alice"


def test_me_without_token_returns_401(client):
    res = client.get("/me")
    assert res.status_code == 401


def test_me_with_invalid_token_returns_401(client):
    res = client.get("/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert res.status_code == 422


# ── /signup alias (frontend route) ───────────────────────────────────────────

def test_signup_alias_returns_token_and_user(client):
    res = client.post(
        "/signup",
        json={
            "username": "carol",
            "password": "secret123",
            "password_confirmation": "secret123",
        },
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["token"]
    assert body["user"]["username"] == "carol"


# ── Notes — unauthenticated access ───────────────────────────────────────────

def test_get_notes_without_token_returns_401(client):
    res = client.get("/notes")
    assert res.status_code == 401


def test_post_note_without_token_returns_401(client):
    res = client.post("/notes", json={"title": "T", "content": "C"})
    assert res.status_code == 401


def test_patch_note_without_token_returns_401(client):
    res = client.patch("/notes/1", json={"title": "T"})
    assert res.status_code == 401


def test_delete_note_without_token_returns_401(client):
    res = client.delete("/notes/1")
    assert res.status_code == 401


# ── Notes — validation ────────────────────────────────────────────────────────

def test_create_note_missing_title_returns_400(client):
    token = get_token(client)
    res = client.post(
        "/notes",
        json={"content": "no title here"},
        headers=auth_headers(token),
    )
    assert res.status_code == 400
    assert res.get_json()["error"]


def test_create_note_missing_content_returns_400(client):
    token = get_token(client)
    res = client.post(
        "/notes",
        json={"title": "no content here"},
        headers=auth_headers(token),
    )
    assert res.status_code == 400
    assert res.get_json()["error"]


# ── Notes — full CRUD + pagination ───────────────────────────────────────────

def test_notes_full_crud_and_pagination(client):
    token = get_token(client)
    headers = auth_headers(token)

    # Create 3 notes
    for i in range(3):
        res = client.post(
            "/notes",
            json={"title": f"Note {i}", "content": f"Body {i}"},
            headers=headers,
        )
        assert res.status_code == 201
        body = res.get_json()
        assert body["title"] == f"Note {i}"
        assert body["content"] == f"Body {i}"
        assert "user_id" in body

    # Paginated list — page 1 of 2
    page = client.get("/notes?page=1&per_page=2", headers=headers)
    assert page.status_code == 200
    payload = page.get_json()
    assert payload["page"] == 1
    assert payload["per_page"] == 2
    assert len(payload["items"]) == 2
    assert payload["total"] == 3
    assert payload["pages"] == 2

    note_id = payload["items"][0]["id"]

    # Read single note
    get_res = client.get(f"/notes/{note_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.get_json()["id"] == note_id

    # Update
    patch_res = client.patch(
        f"/notes/{note_id}", json={"content": "Updated"}, headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.get_json()["content"] == "Updated"

    # Delete
    del_res = client.delete(f"/notes/{note_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.get_json()["message"] == "Note deleted"

    # Confirm gone
    gone = client.get(f"/notes/{note_id}", headers=headers)
    assert gone.status_code == 404


# ── Notes — cross-user isolation ─────────────────────────────────────────────

def test_notes_scoped_to_owner(client):
    """Bob's list must be empty even after Alice creates a note."""
    register(client, "alice", "secret123")
    register(client, "bob", "password456")
    alice_token = login(client, "alice", "secret123").get_json()["access_token"]
    bob_token = login(client, "bob", "password456").get_json()["access_token"]

    client.post(
        "/notes",
        json={"title": "Alice's note", "content": "private"},
        headers=auth_headers(alice_token),
    )

    bob_list = client.get("/notes", headers=auth_headers(bob_token))
    assert bob_list.status_code == 200
    assert bob_list.get_json()["items"] == []


def test_user_cannot_read_update_or_delete_another_users_note(client):
    register(client, "alice", "secret123")
    register(client, "bob", "password456")
    alice_token = login(client, "alice", "secret123").get_json()["access_token"]
    bob_token = login(client, "bob", "password456").get_json()["access_token"]

    create_res = client.post(
        "/notes",
        json={"title": "Private", "content": "Secret"},
        headers=auth_headers(alice_token),
    )
    note_id = create_res.get_json()["id"]

    assert client.get(
        f"/notes/{note_id}", headers=auth_headers(bob_token)
    ).status_code == 404

    assert client.patch(
        f"/notes/{note_id}",
        json={"content": "Hacked"},
        headers=auth_headers(bob_token),
    ).status_code == 404

    assert client.delete(
        f"/notes/{note_id}", headers=auth_headers(bob_token)
    ).status_code == 404
