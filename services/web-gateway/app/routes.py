import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth_proxy import introspect

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


AUTH_URL = "http://auth-service:8000"
ORDER_URL = "http://order-service:8000"


@router.post("/order")
async def create_order(request: Request):
    data = await request.json()
    token = request.cookies.get("access_token") or request.headers.get("Authorization")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{ORDER_URL}/orders/", json=data, headers=headers)
        return r.json(), r.status_code


@router.get("/orders")
async def list_orders(request: Request):
    token = request.cookies.get("access_token") or request.headers.get("Authorization")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    user_id = request.cookies.get("user_id") or "demo"  # fallback for MVP
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDER_URL}/orders/user/{user_id}", headers=headers)
        return r.json(), r.status_code


@router.post("/register")
async def register(request: Request):
    data = await request.json()
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
            msg = r.json().get("detail", "Registration failed.")
            return templates.TemplateResponse(
                "register.html", {"request": request, "message": msg}
            )


@router.post("/login")
async def login(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/auth/token", json=data)
        if r.status_code == 200:
            return RedirectResponse(url="/orders", status_code=303)
        else:
            msg = r.json().get("detail", "Login failed.")
            return templates.TemplateResponse(
                "login.html", {"request": request, "message": msg}
            )


@router.get("/whoami")
async def whoami(request: Request):
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="missing authorization header")
    token = auth.split(" ", 1)[1] if " " in auth else auth
    payload = await introspect(token)
    return payload
