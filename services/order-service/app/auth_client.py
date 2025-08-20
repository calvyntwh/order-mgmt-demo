import os
from typing import Any

import httpx
import structlog

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")


async def introspect_token(token: str, request: Any | None = None) -> dict[str, Any]:
    """Call the Auth Service introspection endpoint and return token claims.

    The Auth service exposes `/introspect` at the root (not under `/auth`).
    """
    headers = {"Authorization": f"Bearer {token}"}
    # inject request id when available for trace propagation
    try:
        from .observability import inject_request_id_headers

        headers = inject_request_id_headers(headers, request)
    except Exception as exc:
        # Non-fatal: record the failure to inject the request id for debugging
        structlog.get_logger().debug("failed to inject request id header", exc_info=exc)

    async with httpx.AsyncClient() as client:
        r = await client.get(f"{AUTH_URL}/introspect", headers=headers, timeout=5.0)
        r.raise_for_status()
        return r.json()
