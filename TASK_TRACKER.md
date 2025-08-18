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
- 🔴 **Critical**: Blocking for other tasks
- 🟡 **High**: Important for success
- 🟢 **Medium**: Nice to have
- ⚪ **Low**: Optional/future

**Status**: ❌ Not Started | 🟡 In Progress | ✅ Complete | 🚫 Blocked

---

## Phase 1: Foundation & Infrastructure Setup (Week 1)

### 1.1 Project Structure Setup
**Priority**: 🔴 Critical | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create monorepo structure following specification | 🔴 | 2h | ✅ | | None | Day 1 |
| [MVP] Set up services/web-gateway directory structure | 🔴 | 1h | ✅ | | Task 1 | Day 1 |
| [MVP] Set up services/auth-service directory structure | 🔴 | 1h | ✅ | | Task 1 | Day 1 |
| [MVP] Set up services/order-service directory structure | 🔴 | 1h | ✅ | | Task 1 | Day 1 |
| [MVP] Initialize pyproject.toml for web-gateway using UV | 🔴 | 1h | ✅ | | Task 2 | Day 1 |
| [MVP] Initialize pyproject.toml for auth-service using UV | 🔴 | 1h | ✅ | | Task 3 | Day 1 |
| [MVP] Initialize pyproject.toml for order-service using UV | 🔴 | 1h | ✅ | | Task 4 | Day 1 |

**Acceptance Criteria**:
- [ ] Monorepo structure matches specification exactly
- [ ] Each service has proper Python 3.13 + UV configuration
- [ ] All pyproject.toml files include required dependencies
- [ ] Directory structure follows naming conventions

---

### 1.2 Database & Infrastructure Setup
**Priority**: 🔴 Critical | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create PostgreSQL init.sql for auth service schema | 🔴 | 2h | ✅ | | None | Day 2 |
| [MVP] Create PostgreSQL init.sql for order service schema | 🔴 | 2h | ✅ | | Task 1 | Day 2 |
| Set up Valkey configuration for session management | 🔴 | 1h | ❌ | | None | Day 2 |
| [MVP] Create base Dockerfile for auth-service | 🔴 | 1.5h | ✅ | | 1.1 Complete | Day 2 |
| [MVP] Create base Dockerfile for order-service | 🔴 | 1.5h | ✅ | | 1.1 Complete | Day 2 |
| [MVP] Create base Dockerfile for web-gateway | 🔴 | 1.5h | ✅ | | 1.1 Complete | Day 2 |
| [MVP] Create Docker Compose with PostgreSQL (Valkey optional for MVP) | 🔴 | 2h | ✅ | | Tasks 1-3 | Day 3 |
| [BACKLOG] Add health checks for all services | 🟡 | 1h | ✅ | | Task 7 | Day 3 |
| [BACKLOG] Configure service networking and discovery | 🔴 | 0.5h | ❌ | | Task 7 | Day 3 |

**Acceptance Criteria**:
- [ ] PostgreSQL initializes with proper schemas for auth and orders
- [ ] Valkey starts correctly with session configuration
- [ ] All services pass health checks
- [ ] Services can communicate via internal networking
- [ ] `docker compose up` completes successfully

---

### 1.3 Development Tooling & Quality Setup
**Priority**: 🟡 High | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Configure Ruff for code formatting across all services | 🟡 | 1h | ✅ | | 1.1 Complete | Day 3 |
| [MVP] Set up BasedPyright for type checking | 🟡 | 1h | 🟡 | | Task 1 | Day 3 |
| Configure pytest with coverage for auth-service | 🟡 | 1h | ❌ | | Task 1 | Day 3 |
| Configure pytest with coverage for order-service | 🟡 | 1h | ❌ | | Task 3 | Day 3 |
| [BACKLOG] Configure pytest with coverage for web-gateway | 🟡 | 1h | ❌ | | Task 4 | Day 3 |
| Set up pre-commit hooks | 🟡 | 0.5h | ❌ | | Tasks 1-2 | Day 4 |
| Create Makefile with development shortcuts | 🟡 | 1.5h | ✅ | | All above | Day 4 |
| [BACKLOG] Configure security scanning with Trivy | 🟡 | 1h | ❌ | | 1.2 Complete | Day 4 |

**Acceptance Criteria**:
- [ ] All linting and formatting tools work across all services
- [ ] Type checking passes with strict configuration
- [ ] Test framework is ready for TDD approach
- [ ] Security scanning pipeline is functional
- [ ] Development workflow is streamlined with make commands

---

### 1.4 Environment Configuration & Security
**Priority**: 🔴 Critical | **Effort**: 4 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create comprehensive .env.example file | 🔴 | 1h | ✅ | | None | Day 4 |
| Set up environment variable validation | 🔴 | 1h | ❌ | | Task 1 | Day 4 |
| Generate secure default secrets for development | 🔴 | 0.5h | ❌ | | Task 1 | Day 4 |
| Configure Structlog logging framework | 🔴 | 1h | ❌ | | Task 1 | Day 5 |
| Set up request ID propagation middleware | 🟡 | 0.5h | ❌ | | Task 4 | Day 5 |

**Acceptance Criteria**:
- [ ] All environment variables are documented and validated
- [ ] Secure secrets are generated for JWT and sessions
- [ ] Structured logging works across all services
- [ ] Request tracing is functional
- [ ] Development environment starts with proper configuration

---

## Phase 2: Authentication Service (Week 2)

### 2.1 User Data Model & Database Layer
**Priority**: 🔴 Critical | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Implement User SQLModel with UUID primary key | 🔴 | 2h | ✅ | | Phase 1 Complete | Day 6 |
| [MVP] Add username field with proper validation | 🔴 | 1h | ✅ | | Task 1 | Day 6 |
| [MVP] Add password_hash field with bcrypt constraints | 🔴 | 1h | ✅ | | Task 2 | Day 6 |
| Add is_admin boolean field with default False | 🔴 | 0.5h | ❌ | | Task 3 | Day 6 |
| Add created_at and last_login timestamp fields | 🔴 | 0.5h | ❌ | | Task 4 | Day 6 |
| Create database connection management with asyncpg | 🔴 | 2h | ❌ | | Task 5 | Day 7 |
| Implement database session handling | 🔴 | 1h | ❌ | | Task 6 | Day 7 |

**Acceptance Criteria**:
- [ ] User model matches specification exactly (UUID, username, password_hash, is_admin, timestamps)
- [ ] Database connections are properly managed and pooled
- [ ] Proper indexes are created for performance
- [ ] Model validation works correctly
- [ ] Database operations are async and efficient

---

### 2.2 Password Security & JWT Implementation
**Priority**: 🔴 Critical | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| Implement bcrypt password hashing with cost factor 12 | 🔴 | 2h | ❌ | | 2.1 Complete | Day 7 |
| Create JWT token generation with proper claims | 🔴 | 3h | ❌ | | Task 1 | Day 8 |
| Implement JWT token validation and verification | 🔴 | 2h | ❌ | | Task 2 | Day 8 |
| Set up token expiration handling (15 minutes) | 🔴 | 1h | ❌ | | Task 3 | Day 8 |
| Create JWT claims structure (sub, username, is_admin, scopes) | 🔴 | 2h | ❌ | | Task 2 | Day 8 |
| Implement secure random secret generation | 🔴 | 1h | ❌ | | None | Day 9 |
| Add JWT ID (jti) for token revocation support | 🟡 | 1h | ❌ | | Task 5 | Day 9 |

**Acceptance Criteria**:
- [ ] Passwords are hashed with bcrypt cost factor 12
- [ ] JWT tokens contain all required claims (sub, username, is_admin, scopes, exp, iat, jti)
- [ ] Token validation is secure and handles edge cases
- [ ] Token expiration works correctly (15 minutes)
- [ ] Security follows industry best practices

---

### 2.3 User Registration & CRUD Operations
**Priority**: 🔴 Critical | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create user registration Pydantic model | 🔴 | 1h | ✅ | | 2.2 Complete | Day 9 |
| [MVP] Implement username validation (4-20 chars, alphanumeric) | 🔴 | 1h | ✅ | | Task 1 | Day 9 |
| [MVP] Implement password validation (min 8 chars) | 🔴 | 1h | ✅ | | Task 2 | Day 9 |
| [MVP] Create user registration endpoint | 🔴 | 2h | ✅ | | Task 3 | Day 10 |
| [MVP] Add username uniqueness checking | 🔴 | 1h | ✅ | | Task 4 | Day 10 |
| Implement proper error handling and responses | 🔴 | 1h | ❌ | | Task 5 | Day 10 |
| Add structured logging for all operations | 🔴 | 1h | ❌ | | Task 6 | Day 10 |

**Acceptance Criteria**:
- [ ] Registration accepts alphanumeric usernames (4-20 chars, unique)
- [ ] Password validation enforces minimum 8 characters
- [ ] Duplicate username prevention with clear error messages
- [ ] All operations are logged with Structlog
- [ ] Input validation prevents injection attacks

---

### 2.4 Authentication Endpoints & Rate Limiting
**Priority**: 🔴 Critical | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Implement OAuth2 password flow endpoint (or a simple token flow for MVP) | 🔴 | 3h | ✅ | | 2.3 Complete | Day 11 |
| [MVP] Create token verification endpoint | 🔴 | 2h | ✅ | | Task 1 | Day 11 |
| [MVP] Implement logout functionality | 🔴 | 2h | ❌ | | Task 2 | Day 11 |
| Add rate limiting for login attempts (5 per minute) | 🔴 | 3h | ❌ | | 1.4 Complete | Day 12 |
| Create proper HTTP status codes and error responses | 🔴 | 1h | ❌ | | Tasks 1-3 | Day 12 |
| Add request/response logging | 🟡 | 1h | ❌ | | Task 5 | Day 12 |

**Acceptance Criteria**:
- [ ] OAuth2 password flow works correctly
- [ ] Token verification returns proper user information
- [ ] Rate limiting prevents brute force attacks (5 attempts/minute)
- [ ] Logout properly invalidates tokens
- [ ] All endpoints return appropriate HTTP status codes

---

### 2.5 Admin User Bootstrap & Testing
**Priority**: 🟡 High | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Implement admin user creation from env vars | 🔴 | 2h | ✅ Complete | | 2.4 Complete | Day 12 |
| Create idempotent bootstrap process | 🔴 | 1h | ✅ Complete | | Task 1 | Day 13 |
| Add unit tests for password hashing | 🟡 | 1h | ❌ | | 2.2 Complete | Day 13 |
| Add unit tests for JWT token operations | 🟡 | 2h | ❌ | | Task 3 | Day 13 |
| Add unit tests for user registration | 🟡 | 1h | ❌ | | Task 4 | Day 13 |
| Add integration tests for auth endpoints | 🟡 | 1h | ❌ | | Task 5 | Day 13 |

**Acceptance Criteria**:
- [ ] Admin user is created from ADMIN_USERNAME and ADMIN_PASSWORD env vars
- [ ] Bootstrap runs idempotently on service startup
- [ ] 90%+ test coverage on critical auth flows
- [ ] All security tests pass
- [ ] Service starts correctly with admin user available

---

## Phase 3: Order Service (Week 3)

### 3.1 Order Data Model & Status Management
**Priority**: 🔴 Critical | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create OrderStatus enum (PENDING, APPROVED, REJECTED) | 🔴 | 1h | ❌ | | Phase 2 Complete | Day 14 |
| [MVP] Implement Order SQLModel with UUID primary key | 🔴 | 2h | ❌ | | Task 1 | Day 14 |
| Add user_id foreign key field with index | 🔴 | 1h | ❌ | | Task 2 | Day 14 |
| Add item_name field with validation (1-255 chars) | 🔴 | 1h | ❌ | | Task 3 | Day 14 |
| Add quantity field with validation (1-100) | 🔴 | 1h | ❌ | | Task 4 | Day 14 |
| Add notes field with validation (max 1000 chars) | 🔴 | 0.5h | ❌ | | Task 5 | Day 15 |
| Add timestamp fields (created_at, updated_at, admin_action_at) | 🔴 | 1h | ❌ | | Task 6 | Day 15 |
| Create database indexes for performance | 🔴 | 0.5h | ❌ | | Task 7 | Day 15 |

**Acceptance Criteria**:
- [ ] Order model matches specification (UUID, user_id, item_name, quantity, notes, status, timestamps)
- [ ] Status transitions are properly managed
- [ ] Proper indexes exist for user_id, status, and created_at
- [ ] Audit trail captures all state changes
- [ ] Model validation prevents invalid data

---

### 3.2 Order CRUD Operations
**Priority**: 🔴 Critical | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create order creation Pydantic model | 🔴 | 1h | ❌ | | 3.1 Complete | Day 15 |
| [MVP] Implement order creation endpoint | 🔴 | 3h | ❌ | | Task 1 | Day 16 |
| [MVP] Create user order history retrieval | 🔴 | 2h | ❌ | | Task 2 | Day 16 |
| Add filtering by status (All, Pending, Approved, Rejected) | 🔴 | 2h | ❌ | | Task 3 | Day 16 |
| Implement pagination for order lists | 🔴 | 2h | ❌ | | Task 4 | Day 17 |
| [MVP] Add order status update functionality | 🔴 | 2h | ❌ | | Task 5 | Day 17 |

**Acceptance Criteria**:
- [ ] Order creation validates item_name (1-255 chars), quantity (1-100), notes (max 1000 chars)
- [ ] Users can only view their own orders
- [ ] Filtering works by status (All, Pending, Approved, Rejected)
- [ ] Pagination handles more than 20 orders
- [ ] Admin status updates are properly logged

---

### 3.3 Authentication Integration & Authorization
**Priority**: 🔴 Critical | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create Auth Service client with HTTPX | 🔴 | 2h | ❌ | | 3.2 Complete | Day 17 |
| [MVP] Implement JWT token validation middleware | 🔴 | 2h | ❌ | | Task 1 | Day 18 |
| Add user context extraction from tokens | 🔴 | 1h | ❌ | | Task 2 | Day 18 |
| Create admin-only endpoint protection | 🔴 | 2h | ❌ | | Task 3 | Day 18 |
| Add scope-based authorization | 🔴 | 1h | ❌ | | Task 4 | Day 18 |

**Acceptance Criteria**:
- [ ] All endpoints verify JWT tokens with Auth Service
- [ ] User context is properly extracted and available
- [ ] Admin endpoints are protected with scope validation
- [ ] Invalid tokens are rejected with proper error messages
- [ ] Service communication is secure and efficient

---

### 3.4 Admin Functions & Order Management
**Priority**: 🟡 High | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Implement admin dashboard data retrieval (minimal) | 🟡 | 2h | ❌ | | 3.3 Complete | Day 19 |
| [MVP] Create order approval endpoint | 🟡 | 2h | ❌ | | Task 1 | Day 19 |
| [MVP] Create order rejection endpoint | 🟡 | 2h | ❌ | | Task 2 | Day 19 |
| Add search functionality by username | 🟡 | 2h | ❌ | | Task 3 | Day 20 |
| Implement CSV export functionality | 🟡 | 3h | ❌ | | Task 4 | Day 20 |
| Add order statistics and reporting | 🟡 | 1h | ❌ | | Task 5 | Day 20 |

**Acceptance Criteria**:
- [ ] Admin dashboard shows all orders with user context
- [ ] One-click approve/reject functionality works
- [ ] Search supports exact and partial username matching
- [ ] CSV export includes all order data
- [ ] Statistics show total orders, pending count, approval rate

---

### 3.5 Testing & Performance Optimization
**Priority**: 🟡 High | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create unit tests for order model validation | 🟡 | 1h | ❌ | | 3.4 Complete | Day 20 |
| Add unit tests for order CRUD operations | 🟡 | 2h | ❌ | | Task 1 | Day 21 |
| Create integration tests with mocked auth service | 🟡 | 2h | ❌ | | Task 2 | Day 21 |
| Add performance tests for order list operations | 🟡 | 1h | ❌ | | Task 3 | Day 21 |
| Optimize database queries and indexing | 🟡 | 2h | ❌ | | Task 4 | Day 21 |

**Acceptance Criteria**:
- [ ] 90%+ test coverage on order management flows
- [ ] Integration tests work with mocked dependencies
- [ ] Order list operations meet performance targets (<100ms p95)
- [ ] Database queries are optimized with proper indexes
- [ ] Service handles errors gracefully

---

## Phase 4: Web Gateway & Frontend (Week 4)

### 4.1 Session Management & Valkey Integration
**Priority**: 🔴 Critical | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| Implement Valkey connection with asyncio-redis | 🔴 | 2h | ❌ | | Phase 3 Complete | Day 22 |
| Create session storage model and operations | 🔴 | 2h | ❌ | | Task 1 | Day 22 |
| Implement session middleware for FastAPI | 🔴 | 3h | ❌ | | Task 2 | Day 23 |
| Add secure cookie configuration | 🔴 | 2h | ❌ | | Task 3 | Day 23 |
| Implement session expiration and sliding window | 🔴 | 2h | ❌ | | Task 4 | Day 23 |
| Add CSRF protection with double-submit pattern | 🔴 | 1h | ❌ | | Task 5 | Day 24 |

**Acceptance Criteria**:
- [ ] Sessions are stored in Valkey with 1-hour TTL
- [ ] Cookies are secure (HttpOnly, Secure, SameSite=Lax)
- [ ] Session data includes user_id, username, jwt_token, csrf_token
- [ ] Sliding window refreshes session on activity
- [ ] CSRF protection prevents cross-site attacks

---

### 4.2 Base Templates & UI Framework Setup
**Priority**: 🟡 High | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create base Jinja2 template with Bulma CSS (minimal styles) | 🟡 | 2h | ❌ | | 4.1 Complete | Day 24 |
| Set up Alpine.js for client-side interactivity | 🟡 | 2h | ❌ | | Task 1 | Day 24 |
| Create navigation component with role-based menus | 🟡 | 2h | ❌ | | Task 2 | Day 25 |
| Implement flash message system | 🟡 | 1h | ❌ | | Task 3 | Day 25 |
| Set up static asset serving (CSS, JS, images) | 🟡 | 1h | ❌ | | Task 4 | Day 25 |

**Acceptance Criteria**:
- [ ] Base template includes Bulma CSS and Alpine.js
- [ ] Template inheritance works correctly
- [ ] Navigation shows appropriate options based on user role
- [ ] Flash messages display correctly for user feedback
- [ ] Static assets (CSS, JS, images) are served efficiently

---

### 4.3 Authentication UI & Forms
**Priority**: 🔴 Critical | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create registration form template | 🔴 | 2h | ❌ | | 4.2 Complete | Day 25 |
| Add client-side validation with Alpine.js | 🔴 | 2h | ❌ | | Task 1 | Day 26 |
| [MVP] Create login form with error handling | 🔴 | 2h | ❌ | | Task 2 | Day 26 |
| Implement logout functionality | 🔴 | 1h | ❌ | | Task 3 | Day 26 |
| Add password strength indicator | 🟡 | 2h | ❌ | | Task 2 | Day 26 |
| Create form validation integration | 🔴 | 3h | ❌ | | Tasks 2-4 | Day 27 |

**Acceptance Criteria**:
- [ ] Registration form validates username (4-20 chars) and password (8+ chars)
- [ ] Login form shows specific error messages for invalid credentials
- [ ] Logout properly clears session and redirects
- [ ] Password strength indicator provides real-time feedback
- [ ] Client-side validation provides immediate user feedback

---

### 4.4 Order Management UI with HTMX
**Priority**: 🔴 Critical | **Effort**: 16 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create order creation form template | 🔴 | 2h | ❌ | | 4.3 Complete | Day 27 |
| [BACKLOG] Add HTMX form submission without page reload | 🔴 | 3h | ❌ | | Task 1 | Day 28 |
| [BACKLOG] Create order history page with filtering | 🔴 | 3h | ❌ | | Task 2 | Day 28 |
| [BACKLOG] Implement real-time status updates with HTMX | 🔴 | 3h | ❌ | | Task 3 | Day 28 |
| [BACKLOG] Create admin dashboard template | 🔴 | 2h | ❌ | | Task 4 | Day 29 |
| [BACKLOG] Add admin approve/reject buttons with HTMX | 🔴 | 2h | ❌ | | Task 5 | Day 29 |
| [BACKLOG] Implement pagination and search UI | 🔴 | 1h | ❌ | | Task 6 | Day 29 |

**Acceptance Criteria**:
- [ ] Order forms submit via HTMX without page reloads
- [ ] Order history updates dynamically with status filters
- [ ] Admin dashboard shows real-time order status changes
- [ ] Pagination works smoothly with HTMX
- [ ] Search functionality provides instant results

---

### 4.5 Service Integration & API Proxying
**Priority**: 🔴 Critical | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create Auth Service API client | 🔴 | 2h | ✅ | | 4.4 Complete | Day 29 |
| [MVP] Create Order Service API client | 🔴 | 2h | ✅ | | Task 1 | Day 30 |
| [BACKLOG] Implement API proxying for auth endpoints | 🔴 | 2h | ❌ | | Task 2 | Day 30 |
| [BACKLOG] Implement API proxying for order endpoints | 🔴 | 2h | ❌ | | Task 3 | Day 30 |

**Acceptance Criteria**:
- [ ] All backend calls are properly proxied through gateway
- [ ] Error messages are user-friendly and informative
- [ ] Service health is monitored and reported
- [ ] Request/response logging aids debugging
- [ ] Timeouts and retries handle service unavailability

---

## Phase 5: Integration & Quality Assurance (Week 5)

### 5.1 End-to-End Testing
**Priority**: 🔴 Critical | **Effort**: 16 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [MVP] Create complete user journey test script (smoke) | 🔴 | 3h | 🟡 | | Phase 4 Complete | Day 31 |
| [BACKLOG] Implement cross-service integration tests | 🔴 | 4h | ❌ | | Task 1 | Day 32 |
| [BACKLOG] Add browser automation tests with Playwright | 🟡 | 4h | ❌ | | Task 2 | Day 32 |
| [BACKLOG] Create load testing for 100 concurrent users | 🟡 | 3h | ❌ | | Task 3 | Day 33 |
| [BACKLOG] Implement chaos testing for service resilience | 🟡 | 2h | ❌ | | Task 4 | Day 33 |

**Acceptance Criteria**:
- [ ] Complete user journey completes in <60 seconds
- [ ] All services communicate correctly under load
- [ ] UI tests cover all critical user flows
- [ ] System supports 100 concurrent users
- [ ] Services gracefully handle failures

---

### 5.2 Security Hardening & Scanning
**Priority**: 🔴 Critical | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [BACKLOG] Run comprehensive security scans with Trivy | 🔴 | 2h | ❌ | | 5.1 Complete | Day 33 |
| [BACKLOG] Fix all HIGH/CRITICAL vulnerabilities | 🔴 | 4h | ❌ | | Task 1 | Day 34 |
| [BACKLOG] Implement comprehensive input sanitization | 🔴 | 2h | ❌ | | Task 2 | Day 34 |
| [BACKLOG] Add XSS prevention measures | 🔴 | 2h | ❌ | | Task 3 | Day 34 |
| [BACKLOG] Perform SQL injection testing | 🔴 | 1h | ❌ | | Task 4 | Day 35 |
| [BACKLOG] Audit authentication security | 🔴 | 1h | ❌ | | Task 5 | Day 35 |

**Acceptance Criteria**:
- [ ] Zero HIGH/CRITICAL vulnerabilities in Trivy scans
- [ ] All inputs are properly sanitized and validated
- [ ] SQL injection attacks are prevented
- [ ] Authentication system passes security audit
- [ ] Rate limiting prevents abuse

---

### 5.3 Performance Optimization
**Priority**: 🟡 High | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [BACKLOG] Optimize database queries and add proper indexes | 🟡 | 2h | ❌ | | 5.2 Complete | Day 35 |
| [BACKLOG] Implement connection pooling optimization | 🟡 | 2h | ❌ | | Task 1 | Day 35 |
| [BACKLOG] Optimize API response times | 🟡 | 2h | ❌ | | Task 2 | Day 36 |
| [BACKLOG] Reduce memory usage across services | 🟡 | 1h | ❌ | | Task 3 | Day 36 |
| [BACKLOG] Optimize container startup times | 🟡 | 1h | ❌ | | Task 4 | Day 36 |

**Acceptance Criteria**:
- [ ] Service startup time <2 seconds
- [ ] Page load time <200ms
- [ ] API response time <100ms p95
- [ ] Memory usage <128MB per service
- [ ] Database queries are optimized

---

### 5.4 Observability & Monitoring
**Priority**: 🟡 High | **Effort**: 12 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| [BACKLOG] Implement comprehensive structured logging | 🟡 | 3h | ❌ | | 5.3 Complete | Day 36 |
| [BACKLOG] Add request tracing across all services | 🟡 | 3h | ❌ | | Task 1 | Day 37 |
| [BACKLOG] Create health check endpoints for all services | 🟡 | 2h | ❌ | | Task 2 | Day 37 |
| [BACKLOG] Add metrics collection and monitoring | 🟡 | 2h | ❌ | | Task 3 | Day 37 |
| [BACKLOG] Implement log aggregation and analysis | 🟡 | 2h | ❌ | | Task 4 | Day 37 |

**Acceptance Criteria**:
- [ ] All actions are logged with structured data
- [ ] Request traces are complete across service boundaries
- [ ] Health checks accurately reflect service status
- [ ] Metrics provide insight into system performance
- [ ] Logs are searchable and actionable

---

## Phase 6: Documentation & Demo Preparation (Week 6)

### 6.1 Comprehensive Documentation
**Priority**: 🟡 High | **Effort**: 16 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| Create detailed README with setup instructions | 🟡 | 4h | ❌ | | Phase 5 Complete | Day 38 |
| Document API specifications and contracts | 🟡 | 4h | ❌ | | Task 1 | Day 39 |
| Create architecture documentation with diagrams | 🟡 | 4h | ❌ | | Task 2 | Day 39 |
| Write troubleshooting and FAQ guides | 🟡 | 2h | ❌ | | Task 3 | Day 40 |
| Document security considerations | 🟡 | 2h | ❌ | | Task 4 | Day 40 |

**Acceptance Criteria**:
- [ ] README enables quick setup and demo in <5 minutes
- [ ] API documentation is complete and accurate
- [ ] Architecture diagrams clearly show service relationships
- [ ] Troubleshooting guide covers common issues
- [ ] Security documentation explains all protections

---

### 6.2 Demo Scripts & Presentation Materials
**Priority**: 🟡 High | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| Create demo script for stakeholder presentation | 🟡 | 2h | ❌ | | 6.1 Complete | Day 40 |
| Prepare sample data and test scenarios | 🟡 | 2h | ❌ | | Task 1 | Day 41 |
| Create presentation slides explaining architecture | 🟡 | 3h | ❌ | | Task 2 | Day 41 |
| Document key features and benefits | 🟡 | 1h | ❌ | | Task 3 | Day 41 |

**Acceptance Criteria**:
- [ ] Demo script completes full user journey in <60 seconds
- [ ] Sample data demonstrates all key features
- [ ] Presentation clearly explains microservices benefits
- [ ] Key features are highlighted with business value

---

### 6.3 Final Testing & Deployment Readiness
**Priority**: 🟡 High | **Effort**: 8 hours | **Status**: ❌

| Task | Priority | Effort | Status | Assignee | Dependencies | Due Date |
|------|----------|---------|---------|-----------|--------------|----------|
| Run final end-to-end validation | 🔴 | 2h | ❌ | | 6.2 Complete | Day 41 |
| Verify all success criteria are met | 🔴 | 2h | ❌ | | Task 1 | Day 42 |
| Create production deployment configurations | 🟢 | 2h | ❌ | | Task 2 | Day 42 |
| Document scaling and operational considerations | 🟢 | 2h | ❌ | | Task 3 | Day 42 |

**Acceptance Criteria**:
- [ ] Docker compose up completes in <5 minutes
- [ ] Complete user journey takes <60 seconds
- [ ] 90%+ test coverage achieved
- [ ] Zero HIGH/CRITICAL security vulnerabilities
- [ ] All performance targets met

---

## Project Success Metrics Dashboard

### Technical Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|---------|
| Setup Time | <5 minutes | TBD | ❌ |
| User Journey Time | <60 seconds | TBD | ❌ |
| Test Coverage | >90% | TBD | ❌ |
| Security Vulnerabilities | 0 HIGH/CRITICAL | TBD | ❌ |
| Service Startup Time | <2 seconds | TBD | ❌ |
| Page Load Time | <200ms | TBD | ❌ |
| API Response Time p95 | <100ms | TBD | ❌ |
| Memory Usage per Service | <128MB | TBD | ❌ |

### Business Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|---------|
| Independent Demo Capability | Yes | TBD | ❌ |
| Microservices Demonstration | Clear | TBD | ❌ |
| Modern Python Practices | Evident | TBD | ❌ |
| Documentation Quality | Excellent | TBD | ❌ |

---

## Risk Tracking

| Risk | Impact | Probability | Mitigation Status | Owner |
|------|--------|-------------|-------------------|-------|
| Service Communication Failures | High | Medium | ❌ Not Started | TBD |
| Authentication Security Issues | High | Low | ❌ Not Started | TBD |
| HTMX Integration Complexity | Medium | Medium | ❌ Not Started | TBD |
| Database Performance Issues | Medium | Low | ❌ Not Started | TBD |
| Container Orchestration Issues | Medium | Low | ❌ Not Started | TBD |

---

## Weekly Milestones

| Week | Milestone | Key Deliverables | Success Criteria |
|------|-----------|------------------|------------------|
| Week 1 | Foundation Complete | Infrastructure, tooling, project structure | All services start with docker compose |
| Week 2 | Auth Service Complete | User registration, login, JWT, admin bootstrap | Users can register and authenticate |
| Week 3 | Order Service Complete | Order CRUD, admin functions, service integration | Orders can be created and managed |
| Week 4 | Frontend Complete | Web gateway, UI, HTMX integration | Complete UI workflow functional |
| Week 5 | Production Ready | Testing, security, performance optimization | All quality gates passed |
| Week 6 | Demo Ready | Documentation, demo scripts, presentation | Stakeholder demo ready |

This task tracker provides a comprehensive breakdown of all implementation tasks with clear priorities, dependencies, effort estimates, and acceptance criteria. It serves as both a project management tool and a quality assurance checklist to ensure the successful delivery of the Order Management Demo App.

## Third-party Reviews — Summary & Immediate Actions

Summary:
- Review 1: Documents are granular and well-structured; recommends CI early, PR/code-review gates, parallel tracks, and a fast-track demo path with de-scoping rules.
- Review 2: Documents are over-engineered for a demo; recommends aggressive scoping down, fewer tests, and a 1–2 week MVP timeline.

Immediate Actions (to implement now):
1. Add CI pipeline task (High) — create GitHub Actions workflow that runs lint, tests, and builds on PRs.
2. Add PR/Code Review gate (High) — require 1 reviewer and pass CI for any merge to main.
3. Add Demo Fast-Track checklist (High) — minimal tasks to deliver a working demo in 2 weeks.

### Demo Fast-Track Checklist (2-week happy-path)
Target: implement minimal happy-path end-to-end demo (register → login → create order → admin approve) in 2 weeks with 1–2 developers.

Week A — Core infra + Auth minimal
- Create monorepo skeleton, minimal pyproject, and Dockerfiles (happy-path only)
- Docker Compose with PostgreSQL and Valkey
- Implement minimal Auth service: user model, registration endpoint, token endpoint (no rate limiting, no blacklisting)
- Add admin bootstrap from env vars
- Basic unit tests for auth happy path

Week B — Orders + Web Gateway minimal
- Implement minimal Order service: create order, list orders for user, admin approve/reject (no search, no CSV)
- Implement Web Gateway: simple templates (no HTMX), proxy login/register and order creation, session cookie using Valkey (basic)
- One end-to-end smoke test for happy path
- Documentation: README with quickstart and demo script

Demo Fast-Track Acceptance:
- End-to-end happy path completes in <60s on local machine
- `docker compose up` starts services and demo runs within ~5 minutes
- Basic tests for happy path present and passing


## MVP Mode: Backlog / De-scoped Items

When running in MVP (2-week) mode, treat the following categories as Backlog and defer implementation until after the demo:
- Performance optimization (Phase 5.3)
- Chaos testing and load testing (Phase 5.1)
- Full security hardening & scans (Phase 5.2)
- Advanced UI features (HTMX real-time updates, pagination, search)
- CSV export, advanced admin reporting
- 90%+ test coverage enforcement (replace with basic smoke/unit tests)

I can now mark these items explicitly as Backlog in the tracker if you want me to apply that tagging across the file.
