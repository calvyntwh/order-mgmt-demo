from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# pydantic BaseModel/Field not needed here; OrderCreate imported from models
from .auth_client import introspect_token
from .db import get_db_pool
from .models import OrderCreate  # centralized Pydantic/SQLModel input model

router = APIRouter(prefix="/orders")

security = HTTPBearer()


def _resolve_pool(get_pool: Any) -> Any:
    """Resolve `get_db_pool` which tests may monkeypatch as either a callable
    (original function) or a pool instance (dummy object).

    Returns the pool instance or None.
    """
    return get_pool() if callable(get_pool) else get_pool


def _row_to_mapping(row: Any, keys: list[str] | None = None) -> dict[str, Any]:
    """Normalize a DB row (mapping or sequence) into a dict[str, Any].

    If `keys` is provided and `row` is a sequence/tuple, keys will be zipped
    with the row values. This centralizes the normalization logic so the
    typechecker sees a single concrete mapping type instead of mixed unknown
    mapping/tuple shapes.
    """
    if row is None:
        return {}
    if isinstance(row, dict):
        raw_map = cast(dict[Any, Any], row)
        return {str(k): v for k, v in raw_map.items()}
    row_tuple = cast(tuple[Any, ...], row)
    if keys is None:
        return {str(i): v for i, v in enumerate(row_tuple)}
    return dict(zip(keys, row_tuple))


async def _execute_fetchone(
    pool: Any, sql: str, params: tuple[Any, ...] | None = None
) -> Any:
    """Execute a query and return a single row. Works with both the real pool
    (connection()/cursor() API) and the test DummyPool (acquire()/fetchrow()).
    """
    params = params or ()
    if hasattr(pool, "acquire"):
        async with pool.acquire() as conn:
            # Dummy test connection exposes fetchrow(sql, params)
            if hasattr(conn, "fetchrow"):
                return await conn.fetchrow(sql, params)
            # otherwise fall back to cursor API
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                return await cur.fetchone()
    else:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                return await cur.fetchone()


async def _execute_fetchall(
    pool: Any, sql: str, params: tuple[Any, ...] | None = None
) -> list[Any]:
    params = params or ()
    if hasattr(pool, "acquire"):
        async with pool.acquire() as conn:
            if hasattr(conn, "fetchall"):
                return await conn.fetchall()
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                return await cur.fetchall()
    else:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                return await cur.fetchall()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    token = credentials.credentials
    try:
        payload = await introspect_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")


async def require_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="admin required")
    return user


CreateOrderIn = OrderCreate


@router.post("/", status_code=201)
async def create_order(
    payload: OrderCreate, user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    pool = _resolve_pool(get_db_pool)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool not available")
    user_id = user.get("sub")
    row = await _execute_fetchone(
        pool,
        "INSERT INTO orders (user_id, item_name, quantity, notes) VALUES (%s,%s,%s,%s) RETURNING id",
        (user_id, payload.item_name, payload.quantity, payload.notes),
    )
    # Dummy fetchrow returns dict-like, real cursor returns tuple
    if row is None:
        return {"id": None}
    if hasattr(row, "get"):
        order_map: dict[str, Any] = _row_to_mapping(row)
    else:
        order_map = _row_to_mapping(row, ["id"])
    id_val = cast(Any, order_map.get("id"))
    return {"id": str(id_val)}


@router.get("/me")
async def list_my_orders(
    user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List orders for the authenticated user."""
    pool = _resolve_pool(get_db_pool)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool not available")
    user_id = user.get("sub")
    rows = await _execute_fetchall(
        pool,
        "SELECT id, item_name, quantity, status, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )
    if rows and isinstance(rows[0], dict):
        normalized: list[dict[str, Any]] = []
        for r in rows:
            r_map: dict[str, Any] = _row_to_mapping(r)
            r_map["id"] = str(cast(Any, r_map.get("id")))
            normalized.append(r_map)
        return normalized
    # sequence rows
    keys = ["id", "item_name", "quantity", "status", "created_at"]
    return [_row_to_mapping(r, keys) for r in rows]


@router.get("/user/{user_id}")
async def list_user_orders(
    user_id: str, user: dict[str, Any] = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """Admin endpoint to list orders for any user. Regular users may only list their own orders."""
    # allow if requester is admin or requesting their own orders
    if user.get("sub") != user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    pool = _resolve_pool(get_db_pool)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool not available")
    rows = await _execute_fetchall(
        pool,
        "SELECT id, item_name, quantity, status, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )
    if rows and isinstance(rows[0], dict):
        normalized: list[dict[str, Any]] = []
        for r in rows:
            r_map: dict[str, Any] = _row_to_mapping(r)
            r_map["id"] = str(cast(Any, r_map.get("id")))
            normalized.append(r_map)
        return normalized
    keys = ["id", "item_name", "quantity", "status", "created_at"]
    return [_row_to_mapping(r, keys) for r in rows]


@router.get("/admin")
async def list_all_orders(
    status: str | None = None, _admin: dict[str, Any] = Depends(require_admin)
) -> list[dict[str, Any]]:
    pool = _resolve_pool(get_db_pool)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool not available")
    if status:
        rows = await _execute_fetchall(
            pool,
            "SELECT id, user_id, item_name, quantity, status, created_at FROM orders WHERE status = %s ORDER BY created_at DESC",
            (status,),
        )
    else:
        rows = await _execute_fetchall(
            pool,
            "SELECT id, user_id, item_name, quantity, status, created_at FROM orders ORDER BY created_at DESC",
        )
    if rows and isinstance(rows[0], dict):
        for r in rows:
            r_map: dict[str, Any] = cast(dict[str, Any], r)
            r_map["id"] = str(cast(Any, r_map.get("id")))
        return rows
    return [
        dict(
            zip(
                ["id", "user_id", "item_name", "quantity", "status", "created_at"],
                [str(r[0])] + list(r[1:]),
            )
        )
        for r in rows
    ]


@router.post("/{order_id}/approve")
async def approve_order(
    order_id: UUID, _admin: dict[str, Any] = Depends(require_admin)
) -> dict[str, Any]:
    pool = _resolve_pool(get_db_pool)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool not available")
    row = await _execute_fetchone(
        pool,
        "UPDATE orders SET status = 'APPROVED', admin_action_at = now(), updated_at = now() WHERE id = %s RETURNING id",
        (str(order_id),),
    )
    if not row:
        raise HTTPException(status_code=404, detail="order not found")
    row_map: dict[str, Any]
    if hasattr(row, "get"):
        row_map = _row_to_mapping(row)
    else:
        row_map = _row_to_mapping(row, ["id"])  # type: ignore[arg-type]
    id_val = cast(Any, row_map.get("id"))
    return {"id": str(id_val), "status": "APPROVED"}


@router.post("/{order_id}/reject")
async def reject_order(
    order_id: UUID, _admin: dict[str, Any] = Depends(require_admin)
) -> dict[str, Any]:
    pool = _resolve_pool(get_db_pool)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool not available")
    row = await _execute_fetchone(
        pool,
        "UPDATE orders SET status = 'REJECTED', admin_action_at = now(), updated_at = now() WHERE id = %s RETURNING id",
        (str(order_id),),
    )
    if not row:
        raise HTTPException(status_code=404, detail="order not found")
    row_map: dict[str, Any]
    if hasattr(row, "get"):
        row_map = _row_to_mapping(row)
    else:
        row_map = _row_to_mapping(row, ["id"])  # type: ignore[arg-type]
    id_val = cast(Any, row_map.get("id"))
    return {"id": str(id_val), "status": "REJECTED"}


@router.get("/{order_id}")
async def get_order(
    order_id: UUID, user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    pool = _resolve_pool(get_db_pool)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool not available")
    row = await _execute_fetchone(
        pool,
        "SELECT id, user_id, item_name, quantity, notes, status, created_at, updated_at, admin_action_at FROM orders WHERE id = %s",
        (str(order_id),),
    )
    if not row:
        raise HTTPException(status_code=404, detail="order not found")
    # Build a well-typed dict[str, Any] regardless of whether the DB returned
    # a mapping (test dummy) or a tuple (real cursor). Declare `order_result`
    # as dict[str, Any] so the analyzer treats it consistently.
    order_result: dict[str, Any]
    if isinstance(row, dict):
        order_result = _row_to_mapping(row)
    else:
        keys = [
            "id",
            "user_id",
            "item_name",
            "quantity",
            "notes",
            "status",
            "created_at",
            "updated_at",
            "admin_action_at",
        ]
        order_result = _row_to_mapping(row, keys)
    # Normalize id and user_id to concrete types before using them
    id_val = cast(Any, order_result.get("id"))
    order_result["id"] = str(id_val)
    user_id_val = cast(Any, order_result.get("user_id"))
    if user_id_val != user.get("sub") and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    return order_result

