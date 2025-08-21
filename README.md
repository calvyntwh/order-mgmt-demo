# Order Management Demo

A small, self-contained demo that shows a minimal microservice architecture for order management. It includes three Python services that demonstrate auth, gateway, and order handling with sensible developer workflows (tests, formatting, linting, and local compose-based orchestration).

This repository is intended for demos, teaching, and local development—not production usage.

## Architecture

- services/auth-service — authentication, session/refresh handling, and JWTs.
- services/order-service — order model, validation, and simple order APIs.
- services/web-gateway — front-end gateway with templates, routes, and an auth proxy that talks to the auth service.
- docker-compose.mvp.yml — a small compose setup used to run the demo locally with a Postgres backing service.

## Quick start (recommended)

Prerequisites:
- Docker & Docker Compose
- Python 3.10+ (for running local tooling and tests)

Start the demo services with Docker Compose (builds images):

```bash
docker compose -f docker-compose.mvp.yml up -d --build
```

Check running containers:

```bash
docker compose -f docker-compose.mvp.yml ps
```

Tail logs for a specific service (example: web-gateway):

```bash
docker compose -f docker-compose.mvp.yml logs -f web-gateway
```

Bring the demo down:

```bash
docker compose -f docker-compose.mvp.yml down
```

## Developer workflow (local tests, formatting, linting)

This repo includes Make targets to run formatters, linters and tests per-service. Examples:

Run all tests across services:

```bash
make test SERVICE=auth-service && make test SERVICE=order-service && make test SERVICE=web-gateway
```

Run formatting and linting across services:

```bash
make format SERVICE=auth-service && make format SERVICE=order-service && make format SERVICE=web-gateway
make lint SERVICE=auth-service && make lint SERVICE=order-service && make lint SERVICE=web-gateway
```

There are convenience VS Code tasks available in the workspace for many of the common commands (see the `tasks` section in the workspace file).

### Running service-specific checks

- Validate auth settings (example shows a missing/empty JWT secret check):

```bash
# fails if JWT_SECRET is not set
env -u JWT_SECRET python -c "from app.settings import settings; settings.validate()"

# quick dev setting for auth service
env JWT_SECRET=dev-secret python -c "from app.settings import settings; settings.validate()"
```

Replace these commands with your preferred virtualenv/poetry invocation if you're running the services locally instead of via Docker.

## Project layout

Top-level folders:

- `services/web-gateway/` — gateway app, templates, static assets, and front-end tests.
- `services/auth-service/` — auth service, DB bootstrap, session store, settings, and tests.
- `services/order-service/` — order service, migrations, and tests.
- `infra/` — infra helpers (Postgres init scripts used by compose/migrations).
- `scripts/` — helper scripts (migrations, e2e smoke scripts, mark_todo_done helper, etc.).
- `docker-compose.mvp.yml` — compose configuration for running the demo locally.

Useful files:

- `todo.md` — demo tracker used by contributors (see `.github/copilot-instructions.md` for guidance).
- `LICENSE` — repository license.

## Tests & Smoke checks

There are unit and integration tests for each service under their respective `tests/` directories. A small suite of higher-level smoke and demo checks live under `tests/` in the repo root and `scripts/e2e_smoke.py`.

Run all tests (fast, per-service):

```bash
make test SERVICE=auth-service
make test SERVICE=order-service
make test SERVICE=web-gateway
```

Or run the combined test task (via the provided VS Code task `test:all` or the Makefile target):

```bash
make test SERVICE=auth-service && make test SERVICE=order-service && make test SERVICE=web-gateway
```

## Development tips

- Use the per-service virtual environment or container for running and debugging.
- `scripts/mark_todo_done.py` is a small helper used to edit `todo.md` during PR workflows.
- The repo includes lightweight instrumentation/observability helpers in each service to make logs and request tracing easier during local development.

## Contributing

Small fixes, improvements and test additions are welcome. When changing public routes or demo behavior, update `todo.md` with a short item describing the change and acceptance steps (see `.github/copilot-instructions.md`).

Suggested PR checklist items:
- Add or update tests for behavior changes
- Update `todo.md` when UX, routes, or demo infra change

## Further reading

- docs/ENVIRONMENT.md — environment and runtime notes
- docs/SECURITY_VERIFICATION.md — security-related verification guidance
- docs/PRD.md — brief product notes and demo goals

## License

See the `LICENSE` file at the repository root.

---

Files created/edited:
- `README.md` — top-level repository README describing purpose, how to run and developer workflows.

Completion status:
- Create README at repo root — Done
