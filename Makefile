# Makefile for MVP workflows

.PHONY: up down logs smoke build lint test. smoke-local

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


lint:
	cd services/auth-service && uv run ruff check .
	cd services/order-service && uv run ruff check .
	cd services/web-gateway && uv run ruff check .

test:
	cd services/auth-service && uv run pytest -q
	cd services/order-service && uv run pytest -q
	cd services/web-gateway && uv run pytest -q

smoke-local:
	cd scripts && uv run python e2e_smoke.py
