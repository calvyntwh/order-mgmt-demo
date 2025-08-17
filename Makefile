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
