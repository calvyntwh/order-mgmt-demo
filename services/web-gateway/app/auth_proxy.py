import os

import httpx

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")


async def introspect(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{AUTH_URL}/auth/introspect", headers=headers, timeout=5.0
        )
        r.raise_for_status()
        return r.json()
