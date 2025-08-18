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
	cd services/web-gateway && uv run djlint templates --check

djlint-fix:
	cd services/web-gateway && uv run djlint templates --fix

