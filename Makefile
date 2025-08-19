# Makefile for MVP workflows

.PHONY: up down logs smoke build lint test smoke-local format lint-fix typecheck coverage djlint djlint-fix

SERVICE ?= auth-service

up:
	docker compose -f docker-compose.mvp.yml up -d --build

down:
	docker compose -f docker-compose.mvp.yml down

logs:
	docker compose -f docker-compose.mvp.yml logs -f

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

typecheck:
	cd services/$(SERVICE) && uv run basedpyright .

coverage:
	cd services/$(SERVICE) && PYTHONPATH=./ uv run pytest --cov=app --cov-report=term-missing

djlint:
	cd services/web-gateway && uv run djlint app/templates --check

djlint-fix:
	cd services/web-gateway && uv run djlint app/templates --reformat

