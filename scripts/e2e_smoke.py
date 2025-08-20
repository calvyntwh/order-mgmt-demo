"""A tiny end-to-end smoke script for local dev.

Note: This script expects the services to be running (docker-compose or local uv run commands).
It is intended as a developer convenience and is not executed by the assistant.
"""
import os
import asyncio
import uuid

import httpx  # type: ignore

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
ORDER_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")


async def run_smoke():
    async with httpx.AsyncClient() as client:
        # register normal user (randomized by default to avoid collisions)
        user_name = os.getenv("SMOKE_USER") or f"smoke-user-{uuid.uuid4().hex[:8]}"
        user_payload = {"username": user_name, "password": "password123"}
        r = await client.post(f"{AUTH_URL}/register", json=user_payload)
        print("register user:", r.status_code)

        # obtain token for normal user
        r = await client.post(f"{AUTH_URL}/token", json=user_payload)
        print("user token:", r.status_code)
        user_token = r.json().get("access_token")
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # create order as normal user
        r = await client.post(
            f"{ORDER_URL}/orders/",
            json={"item_name": "smoke-item", "quantity": 1},
            headers=user_headers,
        )
        print("create order:", r.status_code, r.text)
        order_id = r.json().get("id")
        if order_id is None:
            print("failed to create order; aborting smoke")
            return

        # register admin user (may already exist; ignore 400). Can be overridden with SMOKE_ADMIN
        admin_name = os.getenv("SMOKE_ADMIN") or f"smoke-admin-{uuid.uuid4().hex[:8]}"
        admin_payload = {"username": admin_name, "password": "adminpass123"}
        r = await client.post(f"{AUTH_URL}/register", json=admin_payload)
        print("register admin (may already exist):", r.status_code)

        # Manually promote admin in DB isn't part of this smoke script; many demos ship a seeded admin.
        # Attempt to obtain an admin token (if admin user already has is_admin flag set in DB/seed)
        r = await client.post(f"{AUTH_URL}/token", json=admin_payload)
        print("admin token (may fail if admin not seeded):", r.status_code)
        admin_token = r.json().get("access_token")
        if not admin_token:
            print("admin token not available; smoke will skip approve step")
            return

        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # approve the created order
        r = await client.post(f"{ORDER_URL}/orders/{order_id}/approve", headers=admin_headers)
        print("approve order:", r.status_code, r.text)


if __name__ == "__main__":
    asyncio.run(run_smoke())
