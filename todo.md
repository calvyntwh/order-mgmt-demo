# Order Management Demo - Task Tracker

## Project Overview

**Project**: Simple Order Management Demo App  
**Architecture**: 3-service microservices (Web Gateway, Auth Service, Order Service)  
**Timeline**: 6 weeks  
**Success Criteria**: Complete user journey in <60 seconds with <5 minute setup

## Build-up Approach (use this first)

Follow a "build-up" approach: complete all tasks tagged with [MVP] first. Treat untagged or [BACKLOG]/[EXTENDED] tasks as optional until the MVP is validated. For each completed [MVP] task, open a small PR, add a one-line description of verification steps, and update status.

Quick checklist to follow:

- Focus only on lines prefixed with [MVP].
- Run the local smoke test after finishing each service (auth -> orders -> gateway).
- Keep CI minimal: lint + smoke tests on PRs.
- After end-to-end happy-path works, iterate on BACKLOG items.

---

## Legend

**Status**: [ ] Not Started | [-] In Progress | [x] Complete | 🚫 Blocked

## Recent work (snapshot) — 2025-08-20

- Gateway: updated `services/web-gateway/app/main.py` to accept JSON or form-encoded POSTs for register/login/order flows; set HttpOnly `access_token` cookie on successful login; forward Authorization (from incoming header or cookie) when proxying to order-service; defensively handle non-JSON backend responses to avoid 500 crashes.
- Order-service: fixed route ordering in `services/order-service/app/orders.py` so `/orders/admin` is declared before parameterized `/{order_id}` routes to avoid "admin" being parsed as a UUID (422); the admin route was moved above parameterized routes and admin endpoints now respond correctly.
- Gateway: added a minimal Admin UI (`/admin`) and approve/reject form endpoints that proxy to order-service; added `admin.html` template and navigation link.
- Verification: rebuilt web-gateway, confirmed `/admin` returns HTML, and verified approve/reject flows via the gateway using an admin token — order status updates were observed in the database (APPROVED/REJECTED).

Notes & immediate follow-ups:

- Add an authentication guard for the gateway `/admin` page so unauthenticated users are redirected to `/login`.
- Add CSRF protection for admin form POSTs (or migrate to XHR with CSRF token) to avoid accidental/forged admin actions.
- Harden cookies for production (set Secure flag when TLS present) and integrate Valkey-based session persistence instead of storing raw JWTs in cookies.
- Add a Playwright UI test that exercises register→login→create order→admin approve to prevent regressions.

Status: updates recorded and verified locally — [x] for the items above.

---

## Detailed Task Breakdown (flat checklist)

### Phase 1: Foundation & Infrastructure Setup

- [x] [MVP] Create monorepo structure following specification — Priority: Critical; Effort: 2h; Dependencies: None; Due: Day 1
- [x] [MVP] Set up services/web-gateway directory structure — Priority: Critical; Effort: 1h; Dependencies: Task 1; Due: Day 1
- [x] [MVP] Set up services/auth-service directory structure — Priority: Critical; Effort: 1h; Dependencies: Task 1; Due: Day 1
- [x] [MVP] Set up services/order-service directory structure — Priority: Critical; Effort: 1h; Dependencies: Task 1; Due: Day 1
- [x] [MVP] Initialize pyproject.toml for web-gateway using UV — Priority: Critical; Effort: 1h; Dependencies: Task 2; Due: Day 1
- [x] [MVP] Initialize pyproject.toml for auth-service using UV — Priority: Critical; Effort: 1h; Dependencies: Task 3; Due: Day 1
- [x] [MVP] Initialize pyproject.toml for order-service using UV — Priority: Critical; Effort: 1h; Dependencies: Task 4; Due: Day 1

**Acceptance Criteria:**
- [x] Monorepo structure matches specification exactly
- [x] Each service has proper Python 3.13 + UV configuration
- [x] All pyproject.toml files include required dependencies
- [x] Directory structure follows naming conventions


### Phase 1.2 Database & Infrastructure Setup

- [x] [MVP] Create PostgreSQL init.sql for auth service schema — Priority: Critical; Effort: 2h; Dependencies: None; Due: Day 2
- [x] [MVP] Create PostgreSQL init.sql for order service schema — Priority: Critical; Effort: 2h; Dependencies: Task 1; Due: Day 2
- [ ] Set up Valkey configuration for session management — Priority: Critical; Effort: 1h; Dependencies: None; Due: Day 2
- [x] [MVP] Create base Dockerfile for auth-service — Priority: Critical; Effort: 1.5h; Dependencies: 1.1 Complete; Due: Day 2
- [x] [MVP] Create base Dockerfile for order-service — Priority: Critical; Effort: 1.5h; Dependencies: 1.1 Complete; Due: Day 2
- [x] [MVP] Create base Dockerfile for web-gateway — Priority: Critical; Effort: 1.5h; Dependencies: 1.1 Complete; Due: Day 2
- [-] [MVP] Create Docker Compose with PostgreSQL and Valkey (Valkey required for sessions) — Priority: Critical; Effort: 2h; Dependencies: Tasks 1-3; Due: Day 3
- [x] [BACKLOG] Add health checks for all services — Priority: High; Effort: 1h; Dependencies: Task 7; Due: Day 3
- [ ] [BACKLOG] Configure service networking and discovery — Priority: Critical; Effort: 0.5h; Dependencies: Task 7; Due: Day 3

**Acceptance Criteria:**
- [ ] PostgreSQL initializes with proper schemas for auth and orders
- [ ] Valkey starts correctly with session configuration
- [ ] All services pass health checks
- [ ] Services can communicate via internal networking
- [ ] `docker compose up` completes successfully


### Phase 1.3 Development Tooling & Quality Setup

- [x] [MVP] Configure Ruff for code formatting across all services — Priority: High; Effort: 1h; Dependencies: 1.1 Complete; Due: Day 3
- [-] [MVP] Set up BasedPyright for type checking — Priority: High; Effort: 1h; Dependencies: Task 1; Due: Day 3
- [ ] Configure pytest with coverage for auth-service — Priority: High; Effort: 1h; Dependencies: Task 1; Due: Day 3
- [ ] Configure pytest with coverage for order-service — Priority: High; Effort: 1h; Dependencies: Task 3; Due: Day 3
- [ ] [BACKLOG] Configure pytest with coverage for web-gateway — Priority: High; Effort: 1h; Dependencies: Task 4; Due: Day 3
- [ ] Set up pre-commit hooks — Priority: High; Effort: 0.5h; Dependencies: Tasks 1-2; Due: Day 4
- [x] Create Makefile with development shortcuts — Priority: High; Effort: 1.5h; Dependencies: All above; Due: Day 4
- [ ] [HIGH] Add Trivy CI job for container image scanning — Priority: High; Effort: 1h; Dependencies: 1.2 Complete; Acceptance: documented CI job and remediation checklist; Due: Day 4
- [ ] [BACKLOG] Add Playwright E2E smoke test (headless) — Priority: High; Effort: 3h; Dependencies: Phase 4; Acceptance: headless happy-path runs locally/CI

**Acceptance Criteria:**
- [ ] All linting and formatting tools work across all services
- [ ] Type checking passes with strict configuration
- [ ] Test framework is ready for TDD approach
- [ ] Security scanning pipeline is functional
- [ ] Development workflow is streamlined with make commands


### Phase 1.4 Environment Configuration & Security

- [x] [MVP] Create comprehensive .env.example file — Priority: Critical; Effort: 1h; Dependencies: None; Due: Day 4
- [ ] Set up environment variable validation — Priority: Critical; Effort: 1h; Dependencies: Task 1; Due: Day 4
- [ ] Generate secure default secrets for development — Priority: Critical; Effort: 0.5h; Dependencies: Task 1; Due: Day 4
- [ ] Configure Structlog logging framework — Priority: Critical; Effort: 1h; Dependencies: Task 1; Due: Day 5
- [ ] Set up request ID propagation middleware — Priority: High; Effort: 0.5h; Dependencies: Task 4; Due: Day 5
- [ ] [HIGH] Implement CSRF double‑submit protection for admin & HTMX endpoints — Priority: High; Effort: 1h; Dependencies: Phase 4; Acceptance: admin form POSTs require matching csrf token in session and request; include a small integration test; Due: Day 5
- [ ] [HIGH] Implement login rate limiting in auth-service (5 failed attempts / 60s per username) — Priority: High; Effort: 1h; Dependencies: Auth service ready; Acceptance: 429 response after limit reached and unit test validating behaviour; Due: Day 5
- [ ] [HIGH] Enforce JWT claim structure and bcrypt rounds=12 in auth-service (token expiry 15m) — Priority: High; Effort: 1h; Dependencies: Auth service; Acceptance: token verification endpoint exposes required claims and tests validate bcrypt cost; Due: Day 5

**Acceptance Criteria:**
- [ ] All environment variables are documented and validated
- [ ] Secure secrets are generated for JWT and sessions
- [ ] Structured logging works across all services
- [ ] Request tracing is functional
- [ ] Development environment starts with proper configuration

---

## Post‑MVP / BACKLOG: PRD-derived requirements

Add these PRD-mandated items to the post‑MVP backlog (copy into the canonical tracker above as [BACKLOG] tasks and track verification steps):

- [ ] [BACKLOG] CSRF double‑submit protection for admin & HTMX endpoints — Acceptance: admin form POSTs require matching csrf token present in session and request; include a small integration test.
- [ ] [BACKLOG] Login rate limiting (5 failed attempts / 60s per username) — Acceptance: 429 response after limit reached and unit test validating behaviour.
- [ ] [BACKLOG] Structured logging + X-Request-ID middleware — Acceptance: responses include X-Request-ID header and JSON logs contain request_id.
- [ ] [BACKLOG] Container security scan (Trivy) CI job and remediation checklist — Acceptance: documented CI job and zero HIGH/CRITICAL findings for demo images.
- [ ] [BACKLOG] Playwright E2E: register→login→create order→admin approve — Acceptance: headless test runs locally/CI and verifies happy path.
- [ ] [BACKLOG] Performance benchmark script (API p95 <100ms) and CI smoke test — Acceptance: benchmark script and documented threshold checks.
- [ ] [BACKLOG] SQL injection/parameterized query verification for critical endpoints — Acceptance: tests or linters verifying parameterized queries in auth/order CRUD.
- [ ] [BACKLOG] Test coverage uplift plan to reach 90%+ for critical auth and order flows (define which modules count as "critical") — Acceptance: coverage report showing target reached or a documented mitigation plan.
- [ ] [BACKLOG] Documentation: explicit verification steps (curl commands / sample requests) for each security acceptance criteria so reviewers can reproduce checks.

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