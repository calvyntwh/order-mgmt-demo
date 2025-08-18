import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="web-gateway")
templates = Jinja2Templates(directory="app/templates")

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
async def submit_order(request: Request):
    form = await request.form()
    data = {
        "item_name": form.get("item_name"),
        "quantity": int(form.get("quantity")),
        "notes": form.get("notes") or None,
    }
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:8000/order", json=data)
        if r.status_code == 201:
            message = "Order created successfully."
        else:
            message = r.json().get("detail", "Order creation failed.")
    # Fetch orders after creation
    async with httpx.AsyncClient() as client:
        r_orders = await client.get("http://localhost:8000/orders")
        orders = r_orders.json() if r_orders.status_code == 200 else []
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders, "message": message})


@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    # Fetch orders from backend
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:8000/orders")
        orders = r.json() if r.status_code == 200 else []
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})
