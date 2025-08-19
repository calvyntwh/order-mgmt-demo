import os
from typing import Any, cast

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="web-gateway")
templates = Jinja2Templates(directory="app/templates")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:8002")


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


@app.get("/order", response_class=HTMLResponse)
async def order_page(request: Request):
    return templates.TemplateResponse("order.html", {"request": request})


@app.post("/order", response_class=HTMLResponse)
async def submit_order(request: Request) -> Any:
    form = await request.form()
    quantity_value = form.get("quantity")
    if not isinstance(quantity_value, str):
        quantity_value = "1"  # Default value if not a string
    data = {
        "item_name": form.get("item_name"),
        "quantity": int(quantity_value),
        "notes": form.get("notes") or None,
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{ORDER_SERVICE_URL}/orders", json=data)
        if r.status_code == 201:
            message = "Order created successfully."
        else:
            message = r.json().get("detail", "Order creation failed.")
    # Fetch orders after creation
    async with httpx.AsyncClient() as client:
        r_orders = await client.get(f"{ORDER_SERVICE_URL}/me")
        raw: Any = r_orders.json() if r_orders.status_code == 200 else []
        # Build a concrete list[dict[str, Any]] at runtime so the analyzer
        # sees a consistent shape instead of Any | list[Unknown].
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
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDER_SERVICE_URL}/me")
        raw_payload: Any = r.json() if r.status_code == 200 else []
    orders = _normalize_list(raw_payload)
    for o in orders:
        oid = o.get("id")
        if oid is not None:
            o["id"] = str(oid)
    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders}
    )
