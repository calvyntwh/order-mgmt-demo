# Auth Service

Quick notes

- Tests assume running from inside `services/auth-service` using the per-service environment manager (uv).

Run tests:

```bash
cd services/auth-service
uv run pytest -q
```

Service run (local dev):

```bash
uv run python -m uvicorn app.main:app --reload --port 8000
```

Endpoints of interest:
- POST /auth/register
- POST /auth/token
- GET /auth/introspect  (requires Bearer token)

Env vars:
- DATABASE_URL
- JWT_SECRET
- JWT_ALGORITHM
- JWT_EXPIRE_SECONDS

Notes:
- `GET /auth/introspect` returns token claims and is intended for internal service-to-service token validation in the MVP.
