# Order Service

This is the order microservice for the Order Management Demo.

Quick dev notes

- Tests and runtime commands assume you run them from inside `services/order-service` using the project's per-service environment manager (uv).

Run tests (inside service directory):

```bash
# from services/order-service
uv run pytest -q
```

Service entrypoint for local dev (inside service dir):

```bash
uv run python -m uvicorn app.main:app --reload --port 8001
```

Environment variables the service reads:

- DATABASE_URL - postgres connection string
- JWT_SECRET - secret for validating tokens (dev default: `dev-secret`)
- JWT_ALGORITHM - default `HS256`

Notes

- The endpoints are intentionally minimal for the MVP. Admin endpoints are protected by JWT and require `is_admin` claim to be true in the token payload.
- Tests in `tests/` mock DB and auth dependencies so they can be run without a real DB or auth server.
