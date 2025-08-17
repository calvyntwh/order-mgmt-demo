from fastapi import APIRouter
from pydantic import BaseModel

from .db import get_db_pool

router = APIRouter(prefix="/orders")


class CreateOrderIn(BaseModel):
    user_id: str
    item_name: str
    quantity: int
    notes: str | None = None


@router.post("/", status_code=201)
async def create_order(payload: CreateOrderIn):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO orders (user_id, item_name, quantity, notes) VALUES ($1,$2,$3,$4) RETURNING id",
            payload.user_id,
            payload.item_name,
            payload.quantity,
            payload.notes,
        )
        return {"id": row["id"]}


@router.get("/user/{user_id}")
async def list_user_orders(user_id: str):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, item_name, quantity, status, created_at FROM orders WHERE user_id = $1 ORDER BY created_at DESC", user_id)
        return [dict(r) for r in rows]


@router.post("/{order_id}/approve")
async def approve_order(order_id: str):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("UPDATE orders SET status = 'approved' WHERE id = $1", order_id)
        return {"result": result}


@router.post("/{order_id}/reject")
async def reject_order(order_id: str):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("UPDATE orders SET status = 'rejected' WHERE id = $1", order_id)
        return {"result": result}
