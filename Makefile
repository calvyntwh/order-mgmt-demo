# Makefile for MVP workflows

.PHONY: up down logs smoke build

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
	python -m pip install --upgrade pip && pip install ruff
	ruff check .

test:
	python -m pip install --upgrade pip && pip install -r requirements-dev.txt
	pytest -q services/auth-service/tests
	pytest -q services/order-service/tests
	pytest -q services/web-gateway/tests

smoke-local:
	# Run the local smoke script (expects services to be running locally)
	python scripts/e2e_smoke.py
