import os
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="web-gateway")
templates = Jinja2Templates(directory="app/templates")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:8002")


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
        orders: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    o: dict[str, Any] = {str(k): v for k, v in item.items()}
                    oid = o.get("id")
                    if oid is not None:
                        o["id"] = str(oid)
                    orders.append(o)
    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders, "message": message}
    )


@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request) -> Any:
    # Fetch orders from backend
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDER_SERVICE_URL}/me")
        raw_payload: Any = r.json() if r.status_code == 200 else []
    orders: list[dict[str, Any]] = []
    if isinstance(raw_payload, list):
        for item in raw_payload:
            if isinstance(item, dict):
                o: dict[str, Any] = {str(k): v for k, v in item.items()}
                oid = o.get("id")
                if oid is not None:
                    o["id"] = str(oid)
                orders.append(o)
    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders}
    )
