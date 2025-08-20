import json
import os
import secrets
from typing import Any, cast

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .observability import (
    inject_request_id_headers,
    request_id_middleware,
    setup_logging,
)
from .security import (
    build_auth_headers_from_request,
    get_current_user_optional,
)

setup_logging()
app = FastAPI(title="web-gateway")
app.middleware("http")(request_id_middleware)
templates = Jinja2Templates(directory="app/templates")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:8002")
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:8001")


def _is_secure_cookie(request: Request) -> bool:
    """Decide whether to set Secure=True on cookies.

    Prefer explicit production env or an upstream proxy header indicating TLS.
    """
    if os.environ.get("ENV") == "production":
        return True
    proto = request.headers.get("x-forwarded-proto", "").lower()
    if proto == "https":
        return True
    # Fallback: rely on request.url.scheme if available
    return request.url.scheme == "https"


async def _verify_csrf(request: Request, form: dict | None) -> bool:
    """Double-submit CSRF check for cookie-based authentication.

    Returns True when request is allowed. If an Authorization header is
    present (API client), CSRF is not required. If using cookie-based auth,
    require a matching `csrf_token` form value and `csrf_token` cookie.
    """
    # If client provided Authorization header, assume bearer usage (no CSRF)
    if request.headers.get("Authorization"):
        return True

    # If no access_token cookie, nothing to verify here (anonymous POSTs allowed elsewhere)
    if not request.cookies.get("access_token"):
        return True

    # Ensure form and cookie CSRF tokens match
    if form is None:
        try:
            f = await request.form()
            form = {k: v for k, v in f.items()}
        except (ValueError, RuntimeError):
            return False

    # Accept both plain dicts and FormData-like objects that implement .get()
    cookie_tok = request.cookies.get("csrf_token")
    form_tok = None
    try:
        if isinstance(form, dict):
            form_tok = form.get("csrf_token")
        elif hasattr(form, "get"):
            # starlette.datastructures.FormData exposes .get()
            form_tok = form.get("csrf_token")
    except (AttributeError, TypeError):
        form_tok = None

    return bool(cookie_tok and form_tok and cookie_tok == form_tok)


def _normalize_mapping(obj: Any) -> dict[str, Any]:
    # Prefer concrete dict checks: pyright narrows dict[str, Any] better than
    # collections.abc.Mapping in some configurations. Use dict at runtime and
    # cast to an explicit dict[Any, Any] for iteration.
    if not isinstance(obj, dict):
        return {}
    # Tell the type checker that obj is a dict for iteration. Use a very
    # narrow type-ignore on the assignment so runtime semantics are unchanged
    # and the checker can treat 'mapping' as dict[Any, Any].
    mapping: dict[Any, Any] = obj  # type: ignore[assignment, reportUnknownArgumentType]
    out: dict[str, Any] = {}
    for k, v in mapping.items():
        out[str(k)] = v
    return out


def _normalize_list(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(obj, list):
        return out
    items = cast(list[Any], obj)
    for item in items:
        if isinstance(item, dict):
            out.append(_normalize_mapping(item))
    return out


# auth header building centralized in app/security.py


@app.get("/health")
async def health():
    return {"status": "ok", "service": "web-gateway"}


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/register")
async def register(request: Request) -> Any:
    # Accept JSON or form data from browser
    try:
        data: Any = await request.json()
    except json.JSONDecodeError:
        form = await request.form()
        data = {k: v for k, v in form.items()}

    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(None, request)
        r = await client.post(
            f"{AUTH_SERVICE_URL}/register", json=data, headers=headers
        )
        if r.status_code == 201:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "message": "Registration successful. Please log in.",
                },
            )
        else:
            try:
                msg = r.json().get("detail", "Registration failed.")
            except ValueError:
                msg = "Registration failed."
            return templates.TemplateResponse(
                "register.html", {"request": request, "message": msg}
            )


@app.post("/login")
async def login(request: Request) -> Any:
    try:
        data: Any = await request.json()
    except json.JSONDecodeError:
        form = await request.form()
        data = {k: v for k, v in form.items()}

    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(None, request)
        r = await client.post(f"{AUTH_SERVICE_URL}/token", json=data, headers=headers)
        if r.status_code == 200:
            try:
                token = r.json().get("access_token")
            except ValueError:
                token = None
            response = RedirectResponse(url="/orders", status_code=303)
            if token:
                # set cookie flags: HttpOnly always; Secure when running under TLS/prod
                secure_flag = _is_secure_cookie(request)
                # Set a double-submit CSRF cookie to protect browser form posts
                csrf = secrets.token_urlsafe(32)
                response.set_cookie(
                    key="access_token",
                    value=token,
                    httponly=True,
                    samesite="lax",
                    secure=secure_flag,
                )
                # If upstream issued a refresh_token, persist it in an HttpOnly cookie
                try:
                    refresh = r.json().get("refresh_token")
                except ValueError:
                    refresh = None
                if refresh:
                    response.set_cookie(
                        key="refresh_token",
                        value=refresh,
                        httponly=True,
                        samesite="lax",
                        secure=secure_flag,
                    )
                response.set_cookie(
                    key="csrf_token",
                    value=csrf,
                    httponly=False,
                    samesite="lax",
                    secure=secure_flag,
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


@app.get("/order", response_class=HTMLResponse)
async def order_page(request: Request):
    return templates.TemplateResponse("order.html", {"request": request})


@app.post("/order", response_class=HTMLResponse)
async def submit_order(request: Request) -> Any:
    form = await request.form()
    quantity_value = form.get("quantity")
    if not isinstance(quantity_value, str):
        quantity_value = "1"
    data = {
        "item_name": form.get("item_name"),
        "quantity": int(quantity_value),
        "notes": form.get("notes") or None,
    }

    # Verify CSRF for cookie-based auth
    if not await _verify_csrf(request, form):
        return templates.TemplateResponse(
            "order.html",
            {"request": request, "orders": [], "message": "CSRF verification failed."},
            status_code=403,
        )

    headers = await build_auth_headers_from_request(request)
    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        r = await client.post(
            f"{ORDER_SERVICE_URL}/orders/", json=data, headers=headers
        )
        try:
            raw_err = r.json()
        except ValueError:
            raw_err = None
        message = (
            "Order created successfully."
            if r.status_code == 201
            else (
                raw_err.get("detail")
                if isinstance(raw_err, dict)
                else "Order creation failed."
            )
        )

    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        r_orders = await client.get(f"{ORDER_SERVICE_URL}/orders/me", headers=headers)
        try:
            raw: Any = r_orders.json() if r_orders.status_code == 200 else []
        except ValueError:
            raw = []
        orders = _normalize_list(raw)
        for o in orders:
            oid = o.get("id")
            if oid is not None:
                o["id"] = str(oid)

    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders, "message": message}
    )


@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request) -> Any:
    # Fetch orders from backend
    headers = await build_auth_headers_from_request(request)
    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        r = await client.get(f"{ORDER_SERVICE_URL}/me", headers=headers)
        raw_payload: Any = r.json() if r.status_code == 200 else []
    orders = _normalize_list(raw_payload)
    for o in orders:
        oid = o.get("id")
        if oid is not None:
            o["id"] = str(oid)
    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders}
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request) -> Any:
    """Admin UI: list all orders by calling order-service /orders/admin.

    This page is intended for local/dev admin workflows. It forwards the
    access token stored in the HttpOnly cookie (set at login) or an
    Authorization header when present.
    """

    # Use centralized dependency to optionally retrieve claims. If there is
    # no valid token or introspection fails, `get_current_user_optional` will
    # return None and we'll redirect to login as before.
    claims = await get_current_user_optional(request)
    if not claims:
        return RedirectResponse(url="/login", status_code=303)
    if not claims.get("is_admin"):
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "orders": [],
                "status_code": 403,
                "message": "admin required",
            },
            status_code=403,
        )

    # Build headers for proxying to order-service using the validated token
    headers = await build_auth_headers_from_request(request)

    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        r = await client.get(f"{ORDER_SERVICE_URL}/orders/admin", headers=headers)
        status_code = r.status_code
        try:
            raw: Any = r.json() if status_code == 200 else []
        except ValueError:
            raw = []

    orders = _normalize_list(raw)
    for o in orders:
        oid = o.get("id")
        if oid is not None:
            o["id"] = str(oid)

    return templates.TemplateResponse(
        "admin.html", {"request": request, "orders": orders, "status_code": status_code}
    )


@app.post("/admin/{order_id}/approve")
async def admin_approve(order_id: str, request: Request) -> Any:
    # Use centralized dependency and require admin privileges. We still
    # enforce CSRF for form POSTs when using cookie auth.
    claims = await get_current_user_optional(request)
    if not claims:
        return RedirectResponse(url="/login", status_code=303)
    if not claims.get("is_admin"):
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "orders": [],
                "status_code": 403,
                "message": "admin required",
            },
            status_code=403,
        )

    if not await _verify_csrf(request, None):
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "orders": [],
                "status_code": 403,
                "message": "CSRF verification failed.",
            },
            status_code=403,
        )

    headers = await build_auth_headers_from_request(request)
    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        await client.post(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/approve", headers=headers
        )

    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/{order_id}/reject")
async def admin_reject(order_id: str, request: Request) -> Any:
    claims = await get_current_user_optional(request)
    if not claims:
        return RedirectResponse(url="/login", status_code=303)
    if not claims.get("is_admin"):
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "orders": [],
                "status_code": 403,
                "message": "admin required",
            },
            status_code=403,
        )

    if not await _verify_csrf(request, None):
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "orders": [],
                "status_code": 403,
                "message": "CSRF verification failed.",
            },
            status_code=403,
        )

    headers = await build_auth_headers_from_request(request)
    async with httpx.AsyncClient() as client:
        headers = inject_request_id_headers(headers, request)
        await client.post(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/reject", headers=headers
        )

    return RedirectResponse(url="/admin", status_code=303)


@app.post("/logout")
async def gateway_logout(request: Request) -> Any:
    """Logout endpoint for browser flow: call auth-service /logout then
    clear auth cookies and redirect to login page.
    """
    # Build headers from request to forward token (cookie or Authorization header)
    headers = await build_auth_headers_from_request(request)

    # forward to auth service to mark token revoked
    async with httpx.AsyncClient() as client:
        try:
            headers = inject_request_id_headers(headers, request)
            await client.post(f"{AUTH_SERVICE_URL}/logout", headers=headers)
        except httpx.HTTPError:
            # ignore upstream failures; proceed to clear cookies
            pass

    response = RedirectResponse(url="/login", status_code=303)
    # clear cookies client-side
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    response.delete_cookie("refresh_token")
    return response
