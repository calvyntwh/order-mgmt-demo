# Environment variables & secure dev secrets

This document describes the required environment variables for the Order Management Demo, recommended secure defaults for local development, and guidance for injecting secrets in CI/CD.

IMPORTANT: never commit production secrets to the repository. Use GitHub Actions secrets or your CI provider's secrets store.

## Required variables

- JWT_SECRET (required): secret used to sign JWTs. Minimum recommended entropy: 32 bytes (use a 32+ character base64 string). In production, rotate periodically and store in a secure secret store.
- DATABASE_URL (required): Postgres connection URL used by services and migration helpers (e.g. `postgres://user:pass@host:5432/db`).
- BCRYPT_ROUNDS (recommended): integer cost parameter for bcrypt. For dev, 10-12 is fine; for production, 12+ is recommended.
- VALKEY_URL (optional): URL for the Valkey session store. If not set, the demo falls back to an in-memory session store suitable only for local testing.

## Local development (safe but non-production) `.env.dev` example

Run the validator to generate a suggested `.env.dev`:

```bash
# prints a suggested .env.dev to stdout
./scripts/validate_env.py --suggest
```

Example output (do not use in production):

```text
JWT_SECRET=...random base64...
DATABASE_URL=postgres://postgres:postgres@localhost:5432/demo
BCRYPT_ROUNDS=12
VALKEY_URL=
```

Place the output in `.env.dev` and load it with your preferred tool (e.g., direnv, dotenv loader) for local development.

## CI / GitHub Actions

Use repository secrets to inject sensitive values. Example step snippet for Actions:

```yaml
env:
  DATABASE_URL: ${{ secrets.CI_DATABASE_URL }}
  JWT_SECRET: ${{ secrets.JWT_SECRET }}
  BCRYPT_ROUNDS: ${{ secrets.BCRYPT_ROUNDS }}
  VALKEY_URL: ${{ secrets.VALKEY_URL }}

# Run validator in CI mode to fail fast if secrets are missing
- name: Validate environment
  run: |
    python3 scripts/validate_env.py --ci
```

### Required GitHub Secrets for CI

Make sure the following repository secrets are set for the integration workflow to run successfully:

- `JWT_SECRET` (string, >= 32 chars)
- `DATABASE_URL` (Postgres connection URL used by integration tests)
- `BCRYPT_ROUNDS` (integer, recommended `12`)


If you need ephemeral credentials in CI (for example, creating a test database), generate them during the job and set `DATABASE_URL` accordingly before running the validator.

## Running the validator locally

- Quick check (warnings only):

```bash
./scripts/validate_env.py
```

- CI-safe check (exit code 1 on failure):

```bash
./scripts/validate_env.py --ci
```

- Suggest a developer `.env.dev` file:

```bash
./scripts/validate_env.py --suggest
```

## Notes & recommendations

- Avoid using trivial strings for `JWT_SECRET` such as `dev-secret` in non-development environments. The validator will treat short secrets as weak.
- For production, use a secrets manager (Vault, AWS Secrets Manager, GitHub Secrets) and rotate secrets periodically.
- Consider replacing the static bcrypt seed value used in CI seeding with dynamically-generated hashes during the CI job to avoid committing password hashes to the repo.
