# Makefile for MVP workflows

.PHONY: up down logs logs-follow smoke build lint test smoke-local format lint-fix typecheck coverage djlint djlint-fix

SERVICE ?= auth-service

up:
	docker compose -f docker-compose.mvp.yml up -d --build

down:
	docker compose -f docker-compose.mvp.yml down

LOG_TAIL ?= 200
LOG_SERVICE ?=

# By default `make logs` will show the last $(LOG_TAIL) lines and exit.
# To follow the logs use `make logs-follow` or set LOG_FOLLOW=true and run the follow target.
logs:
	docker compose -f docker-compose.mvp.yml logs --tail=$(LOG_TAIL) $(LOG_SERVICE)

# Follow logs (blocking) - preserves previous behavior but with a configurable tail and optional service
logs-follow:
	docker compose -f docker-compose.mvp.yml logs -f --tail=$(LOG_TAIL) $(LOG_SERVICE)

smoke:
	./scripts/smoke.sh

build:
	docker compose -f docker-compose.mvp.yml build


# Rebuild a single service and restart it (SERVICE must match service directory name, e.g. web-gateway)
.PHONY: rebuild rebuild-all rebuild-auth rebuild-order rebuild-web
rebuild:
	@echo "Rebuilding $(SERVICE)..."
	docker compose -f docker-compose.mvp.yml build $(SERVICE)
	docker compose -f docker-compose.mvp.yml up -d $(SERVICE)

rebuild-all: build
	docker compose -f docker-compose.mvp.yml up -d

# Convenience names for common services
rebuild-auth:
	$(MAKE) SERVICE=auth-service rebuild

rebuild-order:
	$(MAKE) SERVICE=order-service rebuild

rebuild-web:
	$(MAKE) SERVICE=web-gateway rebuild

smoke-local:
	cd scripts && uv run python e2e_smoke.py

format:
	cd services/$(SERVICE) && uv run ruff format .

lint:
	cd services/$(SERVICE) && uv run ruff check .

lint-fix:
	cd services/$(SERVICE) && uv run ruff check . --fix

test:
	cd services/$(SERVICE) && PYTHONPATH=./ uv run pytest


.PHONY: migrate migrate-auth migrate-order
migrate:
	@echo "Run both auth and order SQL initializers against DATABASE_URL"
	python3 scripts/apply_migrations.py --files infra/postgres/init-auth.sql infra/postgres/init-orders.sql

migrate-auth:
	@echo "Apply auth DB init SQL"
	python3 scripts/apply_migrations.py --files infra/postgres/init-auth.sql

migrate-order:
	@echo "Apply order DB init SQL"
	python3 scripts/apply_migrations.py --files infra/postgres/init-orders.sql


.PHONY: test-mark-todo
test-mark-todo:
	@echo "Running mark_todo tests from repo root (uses 'uv run')"
	PYTHONPATH=. uv run pytest tests/test_mark_todo_done.py

typecheck:
	cd services/$(SERVICE) && uv run basedpyright .

coverage:
	cd services/$(SERVICE) && PYTHONPATH=./ uv run pytest --cov=app --cov-report=term-missing

djlint:
	cd services/web-gateway && uv run djlint app/templates --check

djlint-fix:
	cd services/web-gateway && uv run djlint app/templates --reformat

health:
	@echo "Checking services health..."
	@for p in 8000 8001 8002; do printf "port $$p: "; curl -sS --max-time 5 "http://localhost:$$p/health" || echo "FAILED"; echo; done

compose-config:
	docker compose -f docker-compose.mvp.yml config

compose-ps:
	docker compose -f docker-compose.mvp.yml ps

