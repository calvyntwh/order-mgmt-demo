This folder documents the lightweight Alembic usage for per-service migrations.

Usage (local/CI):

- To run both service migrations with Alembic (if installed):

  DATABASE_URL=postgres://user:pass@host:5432/db alembic -c services/auth-service/alembic.ini upgrade head
  DATABASE_URL=postgres://user:pass@host:5432/db alembic -c services/order-service/alembic.ini upgrade head

- The repo also includes SQL initializers under `infra/postgres` used as a fallback when Alembic is not available. The `Makefile` `migrate` targets will prefer Alembic but fall back to `scripts/apply_migrations.py`.

CI recommendation:
- Install `alembic` and `psycopg` in the runner, set `DATABASE_URL` to the test DB, and run the alembic upgrade commands shown above. Optionally apply `infra/postgres/*.sql` before running the services.
