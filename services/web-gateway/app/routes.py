from typing import Any, cast

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth_proxy import introspect

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


AUTH_URL = "http://auth-service:8000"
ORDER_URL = "http://order-service:8000"


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
    except Exception:
        form = await request.form()
        data = {k: v for k, v in form.items()}

    # Token may be stored in a cookie (access_token) or passed via Authorization header
    token_val = request.cookies.get("access_token") or request.headers.get(
        "Authorization"
    )
    headers = {}
    if token_val:
        # If header value already contains 'Bearer ', forward as-is; otherwise prefix
        if str(token_val).lower().startswith("bearer "):
            headers["Authorization"] = str(token_val)
        else:
            headers["Authorization"] = f"Bearer {token_val}"

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{ORDER_URL}/orders/", json=data, headers=headers)
        try:
            raw: Any = r.json()
        except Exception:
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
    token = request.headers.get("Authorization") or request.cookies.get("access_token")
    headers: dict[str, str] = {}
    if token:
        sval = str(token)
        if sval.lower().startswith("bearer "):
            headers["Authorization"] = sval
        else:
            headers["Authorization"] = f"Bearer {sval}"

    # Call the canonical per-user endpoint on order-service. This avoids
    # ambiguity with parameterized routes like `/{order_id}` and matches the
    # recommended canonical route `/orders/me` from the tracker.
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDER_URL}/orders/me", headers=headers)
        try:
            raw: Any = r.json()
        except Exception:
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
    except Exception:
        form = await request.form()
        data = {k: v for k, v in form.items()}

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/auth/register", json=data)
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
            except Exception:
                msg = "Registration failed."
            return templates.TemplateResponse(
                "register.html", {"request": request, "message": msg}
            )


@router.post("/login")
async def login(request: Request) -> Any:
    # Accept JSON or form data
    try:
        data: Any = await request.json()
    except Exception:
        form = await request.form()
        data = {k: v for k, v in form.items()}

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/auth/token", json=data)
        if r.status_code == 200:
            # Extract access token and set as HttpOnly cookie for browser flows
            try:
                token = r.json().get("access_token")
            except Exception:
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
            except Exception:
                msg = "Login failed."
            return templates.TemplateResponse(
                "login.html", {"request": request, "message": msg}
            )


@router.get("/whoami")
async def whoami(request: Request) -> dict[str, Any]:
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="missing authorization header")
    token = auth.split(" ", 1)[1] if " " in auth else auth
    payload: Any = await introspect(token)
    # introspect may return Any; ensure dict[str, Any] for callers
    if not isinstance(payload, dict):
        return {}
    payload_typed = cast(dict[str, Any], payload)
    return {str(k): v for k, v in payload_typed.items()}
