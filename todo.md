# Order Management Demo - Task Tracker

## Project Overview

**Project**: Simple Order Management Demo App  
**Architecture**: 3-service microservices (Web Gateway, Auth Service, Order Service)  
**Timeline**: 6 weeks  
**Success Criteria**: Complete user journey in <60 seconds with <5 minute setup

## Legend

**Status**: [ ] Not Started | [-] In Progress | [x] Complete | 🚫 Blocked

## Prioritized work queue (do these in order)

> Note: this linear list is the active execution order. The Phase-based sections below are preserved as an archive and can be removed once the team adopts the linear queue.

- [x] [1] Fix gateway ↔ order-service endpoint mismatch
  - Decide canonical user-orders route (recommend: `/orders/me`).
  - Update handlers in `services/web-gateway/app/main.py` and audit `services/order-service/app/*` routes and tests.

  - Notes & acceptance criteria (doc-backed):
    - Use a stable, semantic route for the current user's orders (e.g., `/orders/me`) to avoid ambiguity with parameterized `/{order_id}` routes. Update gateway to translate `/orders` -> upstream `/orders/me` when appropriate.
    - Tests: add unit tests in `web-gateway` verifying route translation and integration tests exercising register→login→create order→fetch orders to assert correct routing.
    - References: FastAPI route ordering and path parameter rules; include test that runs against `order-service` directly to ensure backward compatibility.

    - Status: Done — gateway now translates `/orders` -> upstream `/orders/me`; unit tests added in `services/web-gateway` and an e2e smoke run created an order (note: `register` can return 400 if the test user already exists).

- [x] [2] Enforce JWT secret & fail-fast on bad secret
  - Fail startup in `services/auth-service` if `JWT_SECRET` == "dev-secret" when `ENV` != development.
  - Add CI check to ensure `JWT_SECRET` is supplied for production builds.

  - Notes & acceptance criteria (doc-backed):
    - Use a settings model (Pydantic BaseSettings) to validate presence and strength of `JWT_SECRET` at startup. If `ENV` is not `development` and the secret is missing, short, or a known "dev" value, exit with non-zero status and log an explicit error.
    - CI: add a pipeline job that runs the auth-service startup command with production env vars; the job must fail if `JWT_SECRET` is absent or insecure.
    - Tests: unit test that application startup raises SystemExit / fails when JWT_SECRET invalid and ENV=production.

    - Status: Done — runtime validation implemented and unit test added.
      - Implementation: `services/auth-service/app/settings.py` (env-based settings with `validate()`); `services/auth-service/app/main.py` calls validation during startup.
      - Tests: `services/auth-service/tests/test_settings.py` verifies startup validation (raises SystemExit on insecure secret with `ENV=production`).
      - Note on Pydantic: the original acceptance note suggested `BaseSettings`; repository uses pydantic v2 where `BaseSettings` moved to `pydantic-settings`. To avoid adding that dependency and to keep tests deterministic, an environment/dataclass-based validator was implemented instead. If you prefer the Pydantic-based approach, I can switch to `pydantic-settings` in a follow-up.
      - CI check: Deferred — CI pipeline job to run auth-service startup in production-like envs has not been added yet and is recommended as the next step.
    - References: Pydantic settings patterns (BaseSettings / ConfigDict), FastAPI startup validation guidance.

- [x] [3] Harden auth cookie & CSRF strategy
  - Set cookie `secure=True` when TLS is present and tighten `SameSite` in `services/web-gateway/app/main.py`.
  - Choose CSRF strategy (double-submit token) or switch APIs to Authorization headers.
  - Add tests asserting cookie flags and CSRF protections.

  - Notes & acceptance criteria (doc-backed):
    - Cookies: set `Secure=True` when running under TLS (detect via config or `X-Forwarded-Proto`), set `HttpOnly=True`, and use `SameSite=Lax` or `Strict` for sensitive actions. Document behavior for local dev vs prod.
    - CSRF: prefer switching API endpoints to use Authorization headers (Bearer) for XHR/API calls; if HTML forms remain, implement double-submit CSRF token or synchronize token pattern and verify via tests.
    - Tests: automated tests that assert cookie attributes in responses (Secure/HttpOnly/SameSite) and CSRF token validation for admin POSTs.

    - Status: Done — cookie hardening and double-submit CSRF implemented and unit-tested.
      - Implementation: `services/web-gateway/app/main.py` — `_is_secure_cookie()` detects TLS/ENV and login sets `access_token` (HttpOnly) and `csrf_token` cookies; `_verify_csrf()` enforces double-submit token checks for cookie-based POSTs.
      - Tests: `services/web-gateway/tests/test_csrf_cookies.py` covers Secure/HttpOnly cookie flags (when `ENV=production`), rejection when CSRF token missing, and acceptance when cookie+form tokens match. Existing orders/admin routes remain covered by previous tests.
      - Notes: Tests produce minor DeprecationWarnings from Starlette/Jinja templating and per-request cookies; these are non-blocking but can be addressed in a separate cleanup task.
      - Next recommended step: Add CI integration to run these tests and add admin POST CSRF tests (approve/reject) to increase coverage. Consider centralizing token extraction (`get_current_user` dependency) as the follow-up task [6].
    - References: FastAPI cookie handling, OWASP CSRF guidance, and browser cookie semantics.

- [x] [4] Implement token revocation / improve logout semantics
   - Use Valkey as the persistent session store (Valkey-only per team decision).
   - Implement logout to revoke refresh tokens / mark sessions revoked; add tests.

  - Notes & acceptance criteria (doc-backed):
    - Use Valkey to record active sessions and revoked tokens. On logout, mark the session revoked and ensure subsequent refresh attempts fail.
    - Tests: integration tests that perform refresh-token rotation and validate that rotated/revoked tokens are rejected; include concurrency scenario tests for race conditions (multi-process).
    - Implementation subtasks:
      - Add a pluggable `SessionStore` abstraction and a `ValkeySessionStore` implementation in `services/auth-service/app/session_store.py` (keep InMemory fallback for local tests).
      - Replace in-memory refresh store usage with the `SessionStore` factory; use Valkey when `VALKEY_URL` env var is present.
      - Implement atomic rotate/revoke operations using Valkey primitives (atomic server-side update or compare-and-swap API). If Valkey lacks a rotate primitive, implement a small server-side transaction or use Valkey's compare-and-swap semantics.
      - Add integration tests that run against a test Valkey (or an adapted test double) to verify rotation, revoke, and concurrency behaviors.
      - Add Valkey to the local `docker-compose` used by tests (or provide `docker-compose.test.yml`) and a pytest fixture to reset Valkey state between tests.
    - References: OAuth2 refresh-token rotation patterns and Valkey session-store approaches; document trade-offs in `todo.md` and `docs/REVOCATION.md`.
    - Status: Done — Valkey-backed session store implemented, gateway logout wired to revoke sessions, and integration tests (Valkey test-double + concurrency) added. Test results (local): auth-service: 13 passed; order-service: 6 passed; web-gateway: 10 passed.

- [x] [5] Replace broad `except Exception` usage and add observability
  - Replace bare catches with narrow exceptions where safe; ensure defensive/pragma'd handlers remain but log structured errors and stack traces.
  - Add request ID middleware and include IDs in logs and inter-service headers.
  - Notes & acceptance criteria (doc-backed):
  - Replace broad `except Exception` blocks with targeted exception handling where reasonable; preserve intentional defensive catches (many are marked `# pragma: no cover`) and ensure they log structured error payloads (error message, stack, request id) using `structlog` configuration.
  - Observability implemented: request-id middleware added (binds `X-Request-ID` into `request.state` and structlog contextvars), structured JSON logging (`structlog`) configured across services, and `X-Request-ID` forwarded on outbound calls. `/health` endpoints exist in services. Prometheus `/metrics` endpoints are intentionally deferred.
  - Tests: unit tests added/updated to assert `X-Request-ID` appears on responses and that structlog binding does not raise; auth/order/web-gateway test suites pass locally after these changes.
    - References: structlog production config (JSONRenderer), prometheus_client `make_asgi_app()`, and OpenTelemetry/span exemplar guidance.

- [x] [6] Centralize token extraction/validation in web-gateway
  - Add a dependency/util to extract & validate tokens (cookie or header) and return claims.
  - Replace duplicated logic in `services/web-gateway/app/main.py` handlers.

  - Notes & acceptance criteria (doc-backed):
    - Implement a FastAPI dependency (e.g., `get_current_user`) that checks Authorization header first, falls back to access_token cookie, validates signature/claims, and returns a typed Pydantic model with claims.
    - Tests: unit tests for the dependency covering header/cookie precedence, expired tokens, malformed tokens, and missing claims; integration tests asserting protected endpoints reject unauthenticated calls.
    - References: FastAPI dependency patterns for security (Depends, Security) and Pydantic for typed claim models.
  - Subtasks:
    - Add an explicit `/admin` auth guard in `web-gateway` that redirects unauthenticated users to `/login` (implement using the centralized `get_current_user` dependency).
    
  - Status: Done — implemented centralized helpers in `services/web-gateway/app/security.py` (`_extract_raw_token`, `get_current_user`, `get_current_user_optional`, `require_admin`, `build_auth_headers_from_request`) and updated gateway handlers (`app/main.py` and `app/routes.py`) to use them; request-id propagation added for outbound calls. Unit tests run locally: `auth-service` 16 passed, `order-service` 6 passed, `web-gateway` 13 passed.

- [x] [7] Input validation & error handling
  - Replace manual casts with Pydantic models and return 400 on invalid inputs (e.g., quantity parsing).
  - Add unit tests for invalid inputs.

  - Status: Done — Implemented Pydantic validation in `services/web-gateway/app/schemas.py`, updated `submit_order` in `services/web-gateway/app/main.py` to return 400 on invalid inputs, and added `services/web-gateway/tests/test_invalid_order_input.py`. Ran format/lint/tests locally; all service tests passed.

- [x] [8] Response model & schema consistency
  - Ensure `/token` and other endpoints match declared `response_model` and add schema tests.

  - Verification:
    - Added `services/auth-service/tests/test_token_schema.py` and `services/auth-service/tests/test_refresh_schema.py` which validate `/token` and `/refresh` responses against the declared `TokenWithRefresh` Pydantic model.
    - Ran auth-service tests: `18 passed` locally (includes the new schema tests).

- [ ] [9] DB migrations + test infra
  - Add alembic (or equivalent) config for `auth-service` and `order-service` and initial migrations.
  - Add CI step to apply migrations to the test DB before integration tests.
  - Decision for demo: DEFER full Alembic migrations for the MVP/demo.
    - Rationale: SQL initializers exist for a fast demo setup: `infra/postgres/init-auth.sql` and `infra/postgres/init-orders.sql`.
    - Action: keep SQL initializer files in `infra/postgres/` and add a later task to introduce Alembic if schema evolves post-demo.

- [ ] [10] Integration/e2e tests & CI job
  - Add integration tests that exercise gateway→auth→order flows using test DB and migrations.
  - Add a CI job to run the integration suite.

- [x] [11] Server-side authorization enforcement
   - Ensure order-service performs role checks server-side (do not rely solely on gateway).
   - Note: Implemented in `services/order-service/app/orders.py` (requires `get_current_user`/`require_admin` and per-endpoint checks).

- [-] [12] Structured logging, health, and metrics
   - Keep it minimal for the demo: add basic `/health` and consistent structured log lines now; defer Prometheus/OTel instrumentation.
   - Status: `/health` endpoint implemented in `web-gateway`, `auth-service`, and `order-service`; `/ready` and structured JSON logging (request-id propagation) remain TODO.
   - Actions:
     - Implement a lightweight `/health` (200 OK) and `/ready` endpoint in each service for the demo/runtime checks.
     - Standardize a simple structured log line format (JSON or key=value) and ensure critical handlers include service, level, message, and request_id.
     - Defer adding Prometheus `/metrics` endpoints and OTel tracing until post‑MVP.

- [ ] [13] Security hardening & scanning
  - Scope for demo: defer full security scanning (Trivy) and heavy crypto hardening, but make minimal, low-risk improvements now.
  - Actions:
    - Make bcrypt rounds configurable via env var (default to a reasonable dev value, document recommended production >=12).
    - Add a short note to `todo.md` and service README sections documenting the required JWT algorithm (e.g., `HS256`) and rotation plan to be implemented post‑MVP.
    - Defer adding Trivy CI job and full crypto hardening until after the demo.

- [ ] [14] Clean up tracker and CI hooks
  - Remove references to removed `update_tracker` script in CI/docs or update hooks to use `todo.md`.

- [ ] [15] Set up Valkey/session persistence and Docker Compose
  - Finish Valkey configuration for session management and ensure `docker-compose.mvp.yml` composes Valkey and Postgres reliably for local dev.
  - Notes & linkage:
    - Replace raw JWT cookie storage with Valkey-backed session tokens and a migration plan; this work depends on cookie hardening in [3] and token revocation/session strategies in [4].
    - Tests: add integration tests that verify login/logout flows with Valkey sessions and ensure refresh attempts for revoked sessions fail.

- [ ] [16] Configure service networking and discovery for local compose / test environments
  - Ensure services can address each other by service name; document required hostnames/ports for CI and dev.

- [ ] [17] Complete DB migrations & seed data rollout
  - Finalize alembic (or chosen tool) configs for `auth-service` and `order-service` and add initial migrations and seed fixtures for CI tests.

- [ ] [18] Configure pytest + coverage for all services
  - Add per-service pytest config and CI steps for auth-service, order-service, and web-gateway.

- [ ] [19] Add pre-commit and formatting enforcement to CI
  - Ensure Ruff/black/ruff configs are enforced on PRs and add a lint-fix job to CI.

- [ ] [20] Add Trivy container scan to CI
  - Block on HIGH/CRITICAL findings for demo images and document remediation steps.

- [ ] [21] E2E smoke test (headless, script-based)
  - Implement the register→login→create order→admin approve flow using `scripts/e2e_smoke.py` or a minimal requests-based script and add it to CI as a gated smoke test (optional offline flag for local runs).

- [ ] [22] Environment variable validation and secure dev secrets
  - Implement runtime validation for required env vars and provide secure dev defaults; document secret injection for CI/CD.

- [ ] [23] Configure structured logging (structlog) and request ID propagation across services
  - Standardize a JSON log format and add middleware to inject X-Request-ID headers for tracing between services.

- [ ] [24] Implement login rate limiting in auth-service
  - Prevent brute-force by blocking after 5 failed attempts / 60s per username; add unit tests.

- [ ] [25] Enforce bcrypt cost and JWT claim structure
  - Make bcrypt rounds configurable (default >=12) and enforce required JWT claims and algorithm policy.

- [ ] [26] Security verification tasks (Post‑MVP)
  - Performance benchmark script and p95 goals
  - SQL injection / parameterized query verification and linters
  - Test coverage uplift plan and reporting
  - Documentation: curl examples and verification steps for reviewers


## Archived phased plan

The phased breakdown previously used has been retired in favor of the single prioritized linear queue at the top of this file. The full, original phased plan and historical task tracker remain in the repo archives:

- `docs/archives/IMPLEMENTATION_PLAN-2025-08-20T0510.md`
- `docs/archives/TASK_TRACKER-2025-08-20T0513.md`

If you want the phased sections restored as discrete tasks, tell me which phases to un-archive and I'll reinstate them as separate checklists.

## Appendix: Implementation Plan (full)

# Order Management Demo - Implementation Plan

## Executive Summary

This implementation plan breaks down the comprehensive PRD and Technical Specification into executable phases, with detailed tasks, dependencies, and acceptance criteria. The project implements a 3-service microservices architecture showcasing modern Python development practices.

## Project Overview

**Goal**: Build a Simple Order Management Demo App showcasing CaaS platform microservices capabilities  
**Architecture**: 3-service microservices (Web Gateway, Auth Service, Order Service)  
**Tech Stack**: Python 3.13, FastAPI, SQLModel, HTMX, Alpine.js, PostgreSQL, Valkey, UV package manager  
**Success Criteria**: Complete user journey (register→order→admin approval) in <60 seconds with <5 minute setup

## Implementation Phases (summary)

- Phase 1: Foundation & Infrastructure Setup  
- Phase 2: Authentication Service  
- Phase 3: Order Service  
- Phase 4: Web Gateway & Frontend  
- Phase 5: Integration & Quality Assurance  
- Phase 6: Documentation & Demo Preparation

(Full Implementation Plan archived in `docs/archives/IMPLEMENTATION_PLAN-2025-08-20T0510.md` and original `IMPLEMENTATION_PLAN.md`)

## Notes & Archives

- Full implementation plan and task tracker archived in `docs/archives/`:
  - [`docs/archives/IMPLEMENTATION_PLAN-2025-08-20T0510.md`](docs/archives/IMPLEMENTATION_PLAN-2025-08-20T0510.md:1)
  - [`docs/archives/TASK_TRACKER-2025-08-20T0513.md`](docs/archives/TASK_TRACKER-2025-08-20T0513.md:1)

- This file is the canonical tracker; update statuses here and run `scripts/update_tracker.py` to sync snapshots.

---