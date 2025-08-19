import os
from typing import Any

import httpx  # type: ignore

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")


async def introspect_token(token: str) -> dict[str, Any]:
    """Call the Auth Service introspection endpoint and return token claims.

    The Auth service exposes `/introspect` at the root (not under `/auth`).
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{AUTH_URL}/introspect", headers=headers, timeout=5.0)
        r.raise_for_status()
        return r.json()
