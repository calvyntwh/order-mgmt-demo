import base64
import binascii
import os
import time
from collections.abc import Callable
from typing import Any

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# We provide a local permissive stub for psycopg_pool in `types/` so import
# without ignoring; cursor/connection types from `psycopg` are treated as Any.
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from .db import get_db_pool
from .session_store import get_session_store

security = HTTPBearer()
router = APIRouter()

# Simple in-memory token revocation store for MVP/demo.
# This is intentionally lightweight and process-local. For production
# use a centralized session store (Redis, Valkey) so revocations persist
# across processes and restarts.
REVOKED_TOKENS: set[str] = set()


def revoke_token(token: str) -> None:
    """Mark the raw token string as revoked."""
    REVOKED_TOKENS.add(token)


def is_revoked(token: str) -> bool:
    return token in REVOKED_TOKENS


# Pluggable session store (Valkey or in-memory fallback)
SESSION_STORE = get_session_store()
# TTL for refresh tokens (seconds); default 7 days
REFRESH_TTL = int(os.getenv("JWT_REFRESH_EXPIRE_SECONDS", "604800"))


def store_refresh_token(
    refresh_token: str, sub: str, username: str = "", is_admin: bool = False
) -> None:
    session_data = {"sub": sub, "username": username, "is_admin": is_admin}
    SESSION_STORE.store_refresh_token(refresh_token, session_data, REFRESH_TTL)


def revoke_refresh_token(refresh_token: str) -> None:
    SESSION_STORE.revoke_refresh_token(refresh_token)


def is_refresh_revoked(refresh_token: str) -> bool:
    return SESSION_STORE.is_refresh_revoked(refresh_token)


def rotate_refresh_token(old_token: str) -> str | None:
    """Delegate rotation to the session store implementation."""
    return SESSION_STORE.rotate_refresh_token(old_token, REFRESH_TTL)


def _decode_token(token: str) -> dict[str, Any]:
    if is_revoked(token):
        raise HTTPException(status_code=401, detail="token revoked")
    try:
        secret = os.getenv("JWT_SECRET", "dev-secret")
        alg = os.getenv("JWT_ALGORITHM", "HS256")
        return jwt.decode(token, secret, algorithms=[alg])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except jwt.InvalidTokenError:
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


class TokenWithRefresh(TokenOut):
    refresh_token: str


@router.post("/register", status_code=201)
async def register(payload: RegisterIn) -> dict[str, Any]:
    pool: AsyncConnectionPool | None = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="DB pool not available")
    async with pool.connection() as conn:
        cur: Any = conn.cursor()
        async with cur:
            await cur.execute(
                "SELECT id FROM users WHERE username = %s", (payload.username,)
            )
            row: Any = await cur.fetchone()
            if row:
                raise HTTPException(status_code=400, detail="username exists")
            hashed: str = await _hash_password(payload.password)
            await cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (payload.username, hashed),
            )
            return {"username": payload.username}


@router.post("/token", response_model=TokenWithRefresh)
async def token(form: RegisterIn) -> dict[str, Any]:
    pool: AsyncConnectionPool | None = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="DB pool not available")
    async with pool.connection() as conn:
        cur: Any = conn.cursor()
        async with cur:
            await cur.execute(
                "SELECT id, password_hash, is_admin FROM users WHERE username = %s",
                (form.username,),
            )
            row: Any = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="invalid credentials")
            stored: str = row[1]
            if not _verify_password(form.password, stored):
                raise HTTPException(status_code=401, detail="invalid credentials")

            token: str = create_token(
                sub=str(row[0]),
                username=form.username,
                is_admin=bool(row[2]),
            )
            # issue refresh token for session management
            import secrets

            refresh_token = secrets.token_urlsafe(32)
            # record session claims so refresh can issue correct access tokens
            store_refresh_token(
                refresh_token,
                sub=str(row[0]),
                username=form.username,
                is_admin=bool(row[2]),
            )
            return {"access_token": token, "refresh_token": refresh_token}


@router.post("/refresh", response_model=TokenWithRefresh)
async def refresh(payload: dict[str, str]) -> dict[str, Any]:
    """Rotate refresh token and issue a new access token + refresh token.

    Expect JSON: {"refresh_token": "..."}
    """
    old = payload.get("refresh_token")
    if not old:
        raise HTTPException(status_code=400, detail="missing refresh_token")
    if is_refresh_revoked(old):
        raise HTTPException(status_code=401, detail="invalid refresh token")
    # rotate
    new_refresh = rotate_refresh_token(old)
    if new_refresh is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    session = SESSION_STORE.get_session(new_refresh) or {}
    sub = session.get("sub")
    username = session.get("username", "")
    is_admin = session.get("is_admin", False)
    # create new access token using stored session claims
    token = create_token(sub=sub, username=username, is_admin=is_admin)
    return {"access_token": token, "refresh_token": new_refresh}


async def _hash_password(password: str) -> str:
    hashed: bytes = await __to_thread(
        bcrypt.hashpw, password.encode("utf-8"), bcrypt.gensalt()
    )
    # bcrypt returns raw bytes that are not valid UTF-8; store safely using base64
    return base64.b64encode(hashed).decode("ascii")


async def __to_thread(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    import asyncio

    return await asyncio.to_thread(lambda: fn(*args, **kwargs))


def _verify_password(password: str, hashed: str) -> bool:
    try:
        # stored hash is base64-encoded
        decoded = base64.b64decode(hashed.encode("ascii"))
        return bcrypt.checkpw(password.encode("utf-8"), decoded)
    except (binascii.Error, TypeError, ValueError):
        # decoding failed or wrong types; treat as verification failure
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
    return jwt.encode(payload, secret, algorithm=os.getenv("JWT_ALGORITHM", "HS256"))


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
    token = credentials.credentials
    revoke_token(token)
    return {"message": "logged out"}
