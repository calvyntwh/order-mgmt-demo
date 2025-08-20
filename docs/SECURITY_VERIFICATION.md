# Security Verification — Post‑MVP Checklist

This document collects lightweight verification steps for reviewers and CI.
It's intentionally small and safe for inclusion in the demo repo.

## 1) Benchmarking

Use the included `scripts/benchmark.py` to exercise health or API endpoints.
Example:

```bash
./scripts/benchmark.py --url http://localhost:8001/health --n 200
```

Suggested p95 targets (demo-level):
- `/health`: p95 < 200ms
- lightweight API endpoints: p95 < 500ms


## 2) SQL safety quick-scan

Run a quick grep-based scanner to find obvious string concatenation patterns
in Python files that appear near SQL keywords. This is a heuristic and not a
replacement for manual review or static analysis.

```bash
./scripts/sql_safety_check.py
```

If findings appear, review the files and change to parameterized queries using
psycopg pool parameterization or SQLModel/SQLAlchemy bound parameters.


## 3) Coverage uplift plan

Goal: increase branch/statement coverage to 80% across services. Suggested plan:

- Add focused unit tests for error paths in `app/auth.py` and `app/session_store.py`.
- Add integration tests exercising Valkey rotation/revocation flows where possible.
- Add CI gating that fails when per-service coverage drops below 70%.

CI step (example):

```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=services/auth-service --cov-report=xml
    # upload coverage.xml as artifact and fail if below threshold (custom script)
```


## 4) Curl examples and quick manual checks (for reviewers)

Register, login, create an order, and fetch orders (assumes services on localhost):

```bash
# register
curl -X POST -d 'username=test&password=secret' http://localhost:8000/register

# login (returns cookies)
curl -c cookies.txt -X POST -d 'username=test&password=secret' http://localhost:8000/login

# create order using saved cookies
curl -b cookies.txt -X POST -H "Content-Type: application/json" -d '{"item":"widget","qty":1}' http://localhost:8000/orders

# fetch orders
curl -b cookies.txt http://localhost:8000/orders
```

For admin approve flows, ensure an admin user exists or seed one before running.


## 5) Automated linters & static checks

- Run `uv run ruff check . --fix` across services before merging security changes.
- Consider adding `bandit` or `semgrep` for deeper checks as a follow-up.


## 6) Reporting & follow-ups

- If you want, I can add a CI job that runs `scripts/benchmark.py` against a
  deployed preview environment and fails if p95 exceeds thresholds.
- Consider adding a `security/` folder with signed threat-model notes and a
  prioritized remediation backlog.
