import os
import time
from collections.abc import Callable
from typing import Any

import bcrypt  # type: ignore[import]
import jwt  # type: ignore[import]
from fastapi import APIRouter, Depends, HTTPException  # type: ignore[import]
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # type: ignore
from psycopg import AsyncConnection, AsyncCursor  # type: ignore
from psycopg_pool import AsyncConnectionPool  # type: ignore
from pydantic import BaseModel  # type: ignore[import]

from .db import get_db_pool  # type: ignore[import]

security = HTTPBearer()
router = APIRouter()


def _decode_token(token: str) -> dict[str, Any]:
    try:
        secret = os.getenv("JWT_SECRET", "dev-secret")
        alg = os.getenv("JWT_ALGORITHM", "HS256")
        return jwt.decode(token, secret, algorithms=[alg])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    token = credentials.credentials
    return _decode_token(token)


async def require_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="admin required")
    return user


class RegisterIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = (
        "bearer"  # This is a standard OAuth2 token type, not a password  # noqa: S105
    )


@router.post("/register", status_code=201)
async def register(payload: RegisterIn) -> dict[str, Any]:
    pool: AsyncConnectionPool[AsyncConnection] | None = get_db_pool()  # type: ignore[reportUnknownVariableType]
    if pool is None:
        raise HTTPException(status_code=500, detail="DB pool not available")
    conn: AsyncConnection = await pool.connection()  # type: ignore[reportUnknownMemberType]
    async with conn:
        cur: AsyncCursor = conn.cursor()  # type: ignore[reportUnknownMemberType]
        async with cur:
            await cur.execute(
                "SELECT id FROM users WHERE username = %s", (payload.username,)
            )  # type: ignore[reportUnknownMemberType]
            row: Any = await cur.fetchone()  # type: ignore[reportUnknownMemberType]
            if row:
                raise HTTPException(status_code=400, detail="username exists")
            hashed: str = await _hash_password(payload.password)
            await cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (payload.username, hashed),
            )  # type: ignore[reportUnknownMemberType]
            return {"username": payload.username}


@router.post("/token", response_model=TokenOut)
async def token(form: RegisterIn) -> dict[str, Any]:
    pool: AsyncConnectionPool[AsyncConnection] | None = get_db_pool()  # type: ignore[reportUnknownVariableType]
    if pool is None:
        raise HTTPException(status_code=500, detail="DB pool not available")
    conn: AsyncConnection = await pool.connection()  # type: ignore[reportUnknownMemberType]
    async with conn:
        cur: AsyncCursor = conn.cursor()  # type: ignore[reportUnknownMemberType]
        async with cur:
            await cur.execute(
                "SELECT id, password_hash, is_admin FROM users WHERE username = %s",
                (form.username,),
            )  # type: ignore[reportUnknownMemberType]
            row: Any = await cur.fetchone()  # type: ignore[reportUnknownMemberType]
            if not row:
                raise HTTPException(status_code=401, detail="invalid credentials")
            stored: str = row[1]  # type: ignore[reportUnknownVariableType]
            if not _verify_password(form.password, stored):
                raise HTTPException(status_code=401, detail="invalid credentials")

            token: str = create_token(
                sub=str(row[0]),
                username=form.username,
                is_admin=bool(row[2]),
            )  # type: ignore[reportUnknownArgumentType]
            return {"access_token": token}


async def _hash_password(password: str) -> str:
    hashed: bytes = await __to_thread(
        bcrypt.hashpw, password.encode("utf-8"), bcrypt.gensalt()
    )
    return hashed.decode("utf-8")


async def __to_thread(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    import asyncio

    return await asyncio.to_thread(lambda: fn(*args, **kwargs))


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_token(sub: str, username: str, is_admin: bool) -> str:
    secret: str = os.getenv("JWT_SECRET", "dev-secret")
    exp: int = int(time.time()) + int(os.getenv("JWT_EXPIRE_SECONDS", "900"))
    payload: dict[str, Any] = {
        "sub": sub,
        "username": username,
        "is_admin": is_admin,
        "exp": exp,
    }
    return jwt.encode(payload, secret, algorithm=os.getenv("JWT_ALGORITHM", "HS256"))  # type: ignore[reportUnknownArgumentType]


@router.get("/introspect")
async def introspect(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    token: str = credentials.credentials
    payload: dict[str, Any] = _decode_token(token)
    # return token claims for other services to inspect
    return payload


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, str]:
    # For MVP, just accept the token and return success (no blacklist implemented)
    return {"message": "logged out"}
