import os
import httpx
import pytest

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
ORDER_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")

@pytest.mark.asyncio
async def test_happy_path():
    # Register user
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/auth/register", json={"username": "demo", "password": "password123"})
        assert r.status_code == 201
        # Login
        r = await client.post(f"{AUTH_URL}/auth/token", json={"username": "demo", "password": "password123"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Create order
        r = await client.post(f"{ORDER_URL}/orders/", json={"item_name": "widget", "quantity": 2}, headers=headers)
        assert r.status_code == 201
        order_id = r.json()["id"]
        # List user orders
        r = await client.get(f"{ORDER_URL}/orders/user/demo", headers=headers)
        assert r.status_code == 200
        assert any(o["id"] == order_id for o in r.json())
        # Admin approve order (simulate admin)
        admin_token = os.getenv("ADMIN_TOKEN", token)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        r = await client.post(f"{ORDER_URL}/orders/{order_id}/approve", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "APPROVED"
