"""A tiny end-to-end smoke script for local dev.

Note: This script expects the services to be running (docker-compose or local uv run commands).
It is intended as a developer convenience and is not executed by the assistant.
"""
import os
import asyncio

import httpx # type: ignore

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
ORDER_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")


async def run_smoke():
    async with httpx.AsyncClient() as client:
        # register
        r = await client.post(
            f"{AUTH_URL}/register",
            json={"username": "smoke-user", "password": "password123"},
        )
        print("register:", r.status_code)
        # token
        r = await client.post(
            f"{AUTH_URL}/token", json={"username": "smoke-user", "password": "password123"}
        )
        print("token:", r.status_code, r.text)
        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        # create order
        r = await client.post(f"{ORDER_URL}/orders/", json={"item_name": "smoke-item", "quantity": 1}, headers=headers)
        print("create order:", r.status_code, r.text)
        order_id = r.json().get("id")
        if order_id is not None:
            order_id = str(order_id)
            print("created order id:", order_id)


if __name__ == "__main__":
    asyncio.run(run_smoke())
