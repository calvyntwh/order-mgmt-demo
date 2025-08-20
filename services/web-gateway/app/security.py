from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request

from .auth_proxy import introspect


async def _extract_raw_token(request: Request) -> str | None:
    incoming = request.headers.get("Authorization")
    if incoming:
        if incoming.lower().startswith("bearer "):
            return incoming.split(" ", 1)[1]
        return incoming
    return request.cookies.get("access_token")


async def get_current_user(request: Request) -> dict[str, Any]:
    """FastAPI dependency: validate token via auth-service introspection.

    Raises HTTPException(401) when token is missing or invalid.
    Returns a dict of claims on success.
    """
    token = await _extract_raw_token(request)
    if not token:
        raise HTTPException(status_code=401)
    try:
        # introspect uses its own httpx client; keep that behavior.
        # We intentionally do not modify the introspect helper to accept
        # headers in this demo; remove the unused `headers` assignment.
        claims = await introspect(token)
    except httpx.HTTPError:
        raise HTTPException(status_code=401)
    if not isinstance(claims, dict):
        raise HTTPException(status_code=401)
    return claims


async def get_current_user_optional(request: Request) -> dict[str, Any] | None:
    """Like `get_current_user` but returns None instead of raising when
    token is missing or introspection fails. Useful for browser handlers
    that should redirect to the login page instead of returning 401.
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def require_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403)
    return user


async def build_auth_headers_from_request(request: Request) -> dict:
    """Build Authorization headers from the incoming request.

    Prefers an Authorization header, falls back to the `access_token` cookie.
    Returns a dict suitable for passing to httpx requests.
    """
    token_val = request.cookies.get("access_token") or request.headers.get(
        "Authorization"
    )
    headers: dict[str, str] = {}
    if token_val:
        sval = str(token_val)
        if sval.lower().startswith("bearer "):
            headers["Authorization"] = sval
        else:
            headers["Authorization"] = f"Bearer {sval}"
    return headers
