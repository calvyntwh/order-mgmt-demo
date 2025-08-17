#!/usr/bin/env python3
"""
Simple tracker updater: scans for presence of known scaffold files and updates
corresponding task status cells in TASK_TRACKER.md.

Run: python scripts/update_tracker.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_FILE = ROOT / "TASK_TRACKER.md"

# mapping: substring in task row -> (file check function, desired status)
MAPPINGS = {
    "Create monorepo structure following specification": (lambda: (ROOT / "services").exists(), "✅"),
    "Set up services/web-gateway directory structure": (lambda: (ROOT / "services" / "web-gateway").exists(), "✅"),
    "Set up services/auth-service directory structure": (lambda: (ROOT / "services" / "auth-service").exists(), "✅"),
    "Set up services/order-service directory structure": (lambda: (ROOT / "services" / "order-service").exists(), "✅"),
    "Initialize pyproject.toml for web-gateway using UV": (lambda: (ROOT / "services" / "web-gateway" / "pyproject.toml").exists(), "✅"),
    "Initialize pyproject.toml for auth-service using UV": (lambda: (ROOT / "services" / "auth-service" / "pyproject.toml").exists(), "✅"),
    "Initialize pyproject.toml for order-service using UV": (lambda: (ROOT / "services" / "order-service" / "pyproject.toml").exists(), "✅"),
    "Create PostgreSQL init.sql for auth service schema": (lambda: (ROOT / "infra" / "postgres" / "init-auth.sql").exists(), "✅"),
    "Create PostgreSQL init.sql for order service schema": (lambda: (ROOT / "infra" / "postgres" / "init-orders.sql").exists(), "✅"),
    "Create base Dockerfile for auth-service": (lambda: (ROOT / "services" / "auth-service" / "Dockerfile").exists(), "✅"),
    "Create base Dockerfile for order-service": (lambda: (ROOT / "services" / "order-service" / "Dockerfile").exists(), "✅"),
    "Create base Dockerfile for web-gateway": (lambda: (ROOT / "services" / "web-gateway" / "Dockerfile").exists(), "✅"),
    "Create Docker Compose with PostgreSQL (Valkey optional for MVP)": (lambda: (ROOT / "docker-compose.mvp.yml").exists(), "✅"),
    "Create comprehensive .env.example file": (lambda: (ROOT / ".env.example").exists(), "✅"),
    "Create Makefile with development shortcuts": (lambda: (ROOT / "Makefile").exists(), "✅"),
    "Create complete user journey test script (smoke)": (lambda: (ROOT / "scripts" / "smoke.sh").exists(), "🟡"),
    "Add health checks for all services": (lambda: any((ROOT / "services" / s / "app" / "main.py").read_text().find('@app.get("/health")') != -1 for s in ["auth-service","order-service","web-gateway"]), "✅"),
}


def update_task_file():
    text = TASK_FILE.read_text(encoding="utf8")
    lines = text.splitlines()
    changed = False
    for i, line in enumerate(lines):
        for key, (check_fn, status) in MAPPINGS.items():
            if key in line:
                try:
                    result = check_fn()
                except Exception:
                    result = False
                new_status = status if result else None
                if new_status:
                    parts = line.split("|")
                    if len(parts) > 4:
                        old = parts[4]
                        desired = f" {new_status} "
                        if old != desired:
                            parts[4] = desired
                            lines[i] = "|".join(parts)
                            changed = True
    if changed:
        TASK_FILE.write_text("\n".join(lines) + "\n", encoding="utf8")
    return changed


if __name__ == "__main__":
    changed = update_task_file()
    print("TASK_TRACKER.md updated:" , changed)
