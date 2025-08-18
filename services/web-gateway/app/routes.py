import httpx
from fastapi import APIRouter, HTTPException, Request

from .auth_proxy import introspect

router = APIRouter()

AUTH_URL = "http://auth-service:8000"

@router.post("/register")
async def register(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/auth/register", json=data)
        return r.json(), r.status_code

@router.post("/login")
async def login(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/auth/token", json=data)
        return r.json(), r.status_code

@router.get("/whoami")
async def whoami(request: Request):
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="missing authorization header")
    token = auth.split(" ", 1)[1] if " " in auth else auth
    payload = await introspect(token)
    return payload
