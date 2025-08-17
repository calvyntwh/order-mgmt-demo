import os
import time
import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .db import get_db_pool

router = APIRouter(prefix="/auth")


class RegisterIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", status_code=201)
async def register(payload: RegisterIn):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", payload.username)
        if row:
            raise HTTPException(status_code=400, detail="username exists")
        hashed = await _hash_password(payload.password)
        await conn.execute("INSERT INTO users (username, password_hash) VALUES ($1, $2)", payload.username, hashed)
        return {"username": payload.username}


@router.post("/token", response_model=TokenOut)
async def token(form: RegisterIn):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, password_hash, is_admin FROM users WHERE username = $1", form.username)
        if not row:
            raise HTTPException(status_code=401, detail="invalid credentials")
        stored = row["password_hash"]
        if not _verify_password(form.password, stored):
            raise HTTPException(status_code=401, detail="invalid credentials")

        token = _create_token(sub=row["id"], username=form.username, is_admin=row["is_admin"])
        return {"access_token": token}


async def _hash_password(password: str) -> str:
    return (await __to_thread(bcrypt.hashpw, password.encode('utf-8'), bcrypt.gensalt())).decode('utf-8')


async def __to_thread(fn, *args, **kwargs):
    import asyncio

    return await asyncio.to_thread(lambda: fn(*args, **kwargs))


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def _create_token(sub: str, username: str, is_admin: bool) -> str:
    secret = os.getenv("JWT_SECRET", "dev-secret")
    exp = int(time.time()) + int(os.getenv("JWT_EXPIRE_SECONDS", "900"))
    payload = {"sub": sub, "username": username, "is_admin": is_admin, "exp": exp}
    return jwt.encode(payload, secret, algorithm=os.getenv("JWT_ALGORITHM", "HS256"))
