# Notes API

**Author:** Felix Macharia

A secure REST API for managing personal notes, built with Flask and JWT authentication. Each user can only access their own notes — no cross-user data leakage.

---

## Description

The backend is a Flask-RESTful API that supports:

- User registration and login with bcrypt-hashed passwords
- JWT-based authentication (token issued on register/login, sent as a Bearer header on every protected request)
- Full CRUD for a **Notes** resource scoped to the authenticated user
- Paginated listing of notes
- A React frontend (`client-with-jwt/`) that consumes the API

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 16+ (frontend only)

### Backend

```bash
# 1. Clone the repo
git clone https://github.com/Mash-xf/flask-c10-summative-lab-sessions-and-jwt-clients.git
cd flask-c10-summative-lab-sessions-and-jwt-clients

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Apply database migrations
flask --app backend.app db upgrade

# 5. (Optional) Seed sample data — creates users alice and bob
python -m backend.seed
```

### Frontend

```bash
cd client-with-jwt
npm install
```

---

## Running the Application

### Backend API

```bash
# From the repo root, with the virtual environment active:
flask --app backend.app run --port 5555
```

The API will be available at `http://localhost:5555`.

### Frontend

```bash
cd client-with-jwt
npm start          # starts on http://localhost:4000, proxies API calls to :5555
```

### Running Tests

```bash
# From the repo root:
pytest backend/tests/test_api.py -v
```

---

## Environment Variables

| Variable | Default (dev only) | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-me` | Flask session signing key |
| `JWT_SECRET_KEY` | `super-secret-jwt-key-change-me-32b` | JWT signing key (min 32 bytes) |
| `DATABASE_URL` | `sqlite:///backend/app.db` | SQLAlchemy database URI |

Override these in production — never use the defaults outside of local development.

---

## API Endpoints

### Authentication

| Method | Endpoint | Auth required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/register` | No | Create a new account. Returns a JWT token and user object. |
| `POST` | `/signup` | No | Alias for `/register` — used by the React SignUpForm. |
| `POST` | `/login` | No | Authenticate with username and password. Returns a JWT token. |
| `GET` | `/me` | Yes | Return the currently authenticated user. |

#### `POST /register` — request body

```json
{
  "username": "alice",
  "password": "secret123",
  "password_confirmation": "secret123"
}
```

`password_confirmation` is optional on `/register` but required by the frontend `/signup` route.

#### `POST /register` — success response `201`

```json
{
  "message": "User created",
  "token": "<jwt>",
  "user": { "id": 1, "username": "alice" }
}
```

#### `POST /login` — success response `200`

```json
{
  "access_token": "<jwt>",
  "token": "<jwt>",
  "user": { "id": 1, "username": "alice" }
}
```

---

### Notes

All notes endpoints require the JWT in the `Authorization` header:

```
Authorization: Bearer <token>
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/notes` | Paginated list of the authenticated user's notes. |
| `POST` | `/notes` | Create a new note. |
| `GET` | `/notes/<id>` | Fetch a single note by ID. |
| `PATCH` | `/notes/<id>` | Update the title and/or content of a note. |
| `DELETE` | `/notes/<id>` | Delete a note. |

#### `GET /notes` — query parameters

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `page` | `1` | — | Page number (1-based) |
| `per_page` | `10` | `100` | Items per page |

#### `GET /notes` — success response `200`

```json
{
  "items": [
    { "id": 3, "title": "My note", "content": "Some text", "user_id": 1 }
  ],
  "page": 1,
  "per_page": 10,
  "total": 1,
  "pages": 1
}
```

#### `POST /notes` — request body

```json
{ "title": "My note", "content": "Some text" }
```

#### `PATCH /notes/<id>` — request body (all fields optional)

```json
{ "title": "Updated title", "content": "Updated content" }
```

---

### Error Responses

| Status | When |
|--------|------|
| `400` | Missing required fields |
| `401` | Missing or invalid credentials / no token provided |
| `404` | Note not found or belongs to another user |
| `409` | Username already taken |
| `422` | Malformed JWT token |

---

## Project Structure

```
.
├── backend/
│   ├── app.py              # Application factory
│   ├── config.py           # Configuration (reads from env vars)
│   ├── models.py           # SQLAlchemy models: User, Note
│   ├── routes.py           # Flask-RESTful resource classes
│   ├── seed.py             # Sample data for development
│   ├── requirements.txt    # Python dependencies
│   ├── migrations/         # Alembic migration scripts
│   └── tests/
│       ├── conftest.py     # pytest fixtures and shared helpers
│       └── test_api.py     # API contract and auth-flow tests
└── client-with-jwt/        # React frontend
    └── src/
        └── components/
            ├── App.js
            ├── Notes.js    # Full CRUD UI for notes
            ├── LoginForm.js
            ├── SignUpForm.js
            └── NavBar.js
```
