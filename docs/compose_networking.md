# Compose networking and service hostnames

This document explains how services in `docker-compose.mvp.yml` address one another
in local development and CI runs.

Key points
- Services are attached to the `order_mgmt_network` Docker network (bridge driver).
- Each service exposes one or more network aliases so they can be reached by stable hostnames.

Service hostnames (examples)
- auth-service: `auth-service` or `auth` (ports: 8001 on host -> 8001 in container)
- order-service: `order-service` or `order` (ports: 8002 on host -> 8002 in container)
- web-gateway: `web-gateway` or `web` (ports: 8000 on host -> 8000 in container)
- valkey: `valkey` (port 6379)
- postgres: `postgres` (port 5432)

Usage notes
- From inside containers you should use the service name (e.g. `http://auth-service:8001`) rather than `localhost`.
- CI runners that spawn the compose stack should be careful about port collisions on the host. If the runner needs parallel jobs, prefer ephemeral ports or task-scoped networks.

Healthchecks & depends_on
- `depends_on` uses Docker Compose's `condition: service_healthy` to ensure startup ordering.
- Tests and CI should still wait for health endpoints to respond; see `scripts/wait_for_services.sh` for a helper.

Port mapping summary
- Host 8000 -> `web-gateway:8000`
- Host 8001 -> `auth-service:8001`
- Host 8002 -> `order-service:8002`
- Host 5432 -> `postgres:5432`
- Host 6379 -> `valkey:6379`

Examples
- From inside `order-service` container to call auth-service: `http://auth-service:8001/token`
- From `web-gateway` to call order-service: `http://order-service:8002/orders`

Troubleshooting
- If a service cannot resolve another service hostname, verify that both services are on the same network:
  `docker network inspect order_mgmt_network`.
- If ports are in use on the host, adjust the host mapping in `docker-compose.mvp.yml` before running `docker compose up`.
