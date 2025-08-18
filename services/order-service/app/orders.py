from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, conint, constr

from .auth_client import introspect_token
from .db import get_db_pool

router = APIRouter(prefix="/orders")

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, Any]:
    token = credentials.credentials
    try:
        payload = await introspect_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")


async def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="admin required")
    return user

class CreateOrderIn(BaseModel):
    item_name: constr(min_length=1, max_length=255)
    quantity: conint(ge=1, le=100)
    notes: constr(max_length=1000) | None = None


@router.post("/", status_code=201)
async def create_order(payload: CreateOrderIn, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    pool = get_db_pool()
    user_id = user.get("sub")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO orders (user_id, item_name, quantity, notes) VALUES ($1,$2,$3,$4) RETURNING id",
            user_id,
            payload.item_name,
            payload.quantity,
            payload.notes,
        )
        return {"id": row["id"]}


@router.get("/user/{user_id}")
async def list_user_orders(user_id: str) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, item_name, quantity, status, created_at FROM orders WHERE user_id = $1 ORDER BY created_at DESC", user_id)
        return [dict(r) for r in rows]


@router.post("/{order_id}/approve")
async def approve_order(order_id: str, _admin: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE orders SET status = 'APPROVED', admin_action_at = now(), updated_at = now() WHERE id = $1 RETURNING id",
            order_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="order not found")
        return {"id": row["id"], "status": "APPROVED"}


@router.post("/{order_id}/reject")
async def reject_order(order_id: str, _admin: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE orders SET status = 'REJECTED', admin_action_at = now(), updated_at = now() WHERE id = $1 RETURNING id",
            order_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="order not found")
        return {"id": row["id"], "status": "REJECTED"}



@router.get("/{order_id}")
async def get_order(order_id: str, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, user_id, item_name, quantity, notes, status, created_at, updated_at, admin_action_at FROM orders WHERE id = $1",
            order_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="order not found")
        # allow owners or admins
        if row["user_id"] != user.get("sub") and not user.get("is_admin"):
            raise HTTPException(status_code=403, detail="forbidden")
        return dict(row)


@router.get("/admin")
async def list_all_orders(status: str | None = None, _admin: dict[str, Any] = Depends(require_admin)) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT id, user_id, item_name, quantity, status, created_at FROM orders WHERE status = $1 ORDER BY created_at DESC",
                status,
            )
        else:
            rows = await conn.fetch(
                "SELECT id, user_id, item_name, quantity, status, created_at FROM orders ORDER BY created_at DESC"
            )
        return [dict(r) for r in rows]
