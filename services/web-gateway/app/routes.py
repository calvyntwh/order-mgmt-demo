import json
import os
from typing import Any, cast

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .observability import inject_request_id_headers
from .security import build_auth_headers_from_request, get_current_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:8001")
ORDER_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:8002")


def _normalize_mapping(obj: Any) -> dict[str, Any]:
    """Return a concrete mapping with string keys from a runtime value.

    This is a permissive runtime shim that converts arbitrary dict-like JSON
    results into typed dict[str, Any] so the static analyzer sees a concrete
    shape before callers use .get or mutate the mapping.
    """
    if not isinstance(obj, dict):
        return {}
    # Tell the type checker that obj is a dict for iteration. This narrow
    # type-ignore avoids passing an untyped Any into dict() constructors.
    mapping: dict[Any, Any] = obj  # type: ignore[assignment, reportUnknownArgumentType]
    out: dict[str, Any] = {}
    for k, v in mapping.items():
        out[str(k)] = v
    return out


def _normalize_list(obj: Any) -> list[dict[str, Any]]:
    """Return a concrete list of mappings from a runtime value.

    Accepts any runtime value and returns an empty list if it's not a list.
    """
    out: list[dict[str, Any]] = []
    if not isinstance(obj, list):
        return out
    items = cast(list[Any], obj)
    for item in items:
        if isinstance(item, dict):
            out.append(_normalize_mapping(item))
    return out


@router.post("/order")
async def create_order(request: Request) -> tuple[dict[str, Any] | None, int]:
    # Accept JSON body (fetch/XHR) or HTML form submissions
    try:
        data: Any = await request.json()
    except (ValueError, json.JSONDecodeError):
        # request.json() may raise JSONDecodeError or ValueError for invalid bodies;
        # fall back to form parsing for browser form submissions.
        form = await request.form()
        data = {k: v for k, v in form.items()}

    # Build headers from incoming request using centralized helper. This
    # preserves consistent behavior for cookie vs header extraction.
    headers = await build_auth_headers_from_request(request)
    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        r = await client.post(f"{ORDER_URL}/orders/", json=data, headers=headers)
        try:
            raw: Any = r.json()
        except ValueError:
            raw = None
        payload: dict[str, Any] | None = None
        if raw is not None:
            payload = _normalize_mapping(raw)
        # Normalize id to string if present and return a concrete mapping
        if payload:
            oid = payload.get("id")
            if oid is not None:
                payload["id"] = str(oid)
            # Ensure we return a dict[str, Any] with concrete string keys
            return ({str(k): v for k, v in payload.items()}, r.status_code)
        return None, r.status_code


@router.get("/orders")
async def list_orders(request: Request) -> tuple[list[dict[str, Any]], int]:
    # Prefer Authorization header first, fall back to access_token cookie. If a
    # bare token value is provided (cookie), prefix with 'Bearer '. This keeps
    # the gateway behavior consistent with other handlers that forward tokens.
    headers = await build_auth_headers_from_request(request)
    # Call the canonical per-user endpoint on order-service. This avoids
    # ambiguity with parameterized routes like `/{order_id}` and matches the
    # recommended canonical route `/orders/me` from the tracker.
    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        r = await client.get(f"{ORDER_URL}/orders/me", headers=headers)
        try:
            raw: Any = r.json()
        except ValueError:
            raw = []
        payload = _normalize_list(raw)
        # Normalize any returned order ids to strings and return concrete list
        orders: list[dict[str, Any]] = []
        for o in payload:
            oid = o.get("id")
            if oid is not None:
                o["id"] = str(oid)
            orders.append(dict(o))
        return orders, r.status_code


@router.post("/register")
async def register(request: Request) -> Any:
    # Accept JSON or form data
    try:
        data: Any = await request.json()
    except (ValueError, json.JSONDecodeError):
        # request.json() may raise JSONDecodeError or ValueError for invalid bodies;
        # fall back to form parsing for browser form submissions.
        form = await request.form()
        data = {k: v for k, v in form.items()}

    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(None, request)
        r = await client.post(f"{AUTH_URL}/auth/register", json=data, headers=headers)
        if r.status_code == 201:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "message": "Registration successful. Please log in.",
                },
            )
        else:
            # Defensive parsing of error message
            try:
                msg = r.json().get("detail", "Registration failed.")
            except ValueError:
                msg = "Registration failed."
            return templates.TemplateResponse(
                "register.html", {"request": request, "message": msg}
            )


@router.post("/login")
async def login(request: Request) -> Any:
    # Accept JSON or form data
    try:
        data: Any = await request.json()
    except (ValueError, json.JSONDecodeError):
        form = await request.form()
        data = {k: v for k, v in form.items()}

    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(None, request)
        r = await client.post(f"{AUTH_URL}/auth/token", json=data, headers=headers)
        if r.status_code == 200:
            # Extract access token and set as HttpOnly cookie for browser flows
            try:
                token = r.json().get("access_token")
            except ValueError:
                token = None
            response = RedirectResponse(url="/orders", status_code=303)
            if token:
                # In production use secure=True and proper SameSite depending on requirements
                response.set_cookie(
                    key="access_token",
                    value=token,
                    httponly=True,
                    samesite="lax",
                )
            return response
        else:
            try:
                msg = r.json().get("detail", "Login failed.")
            except ValueError:
                msg = "Login failed."
            return templates.TemplateResponse(
                "login.html", {"request": request, "message": msg}
            )


@router.get("/whoami")
async def whoami(request: Request) -> dict[str, Any]:
    # Use centralized introspection via get_current_user dependency. This
    # will raise HTTPException(401) on missing/invalid tokens which matches
    # previous behavior.
    payload = await get_current_user(request)
    if not isinstance(payload, dict):
        return {}
    payload_typed = cast(dict[str, Any], payload)
    return {str(k): v for k, v in payload_typed.items()}
