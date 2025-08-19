import os
from typing import Any

from psycopg_pool import AsyncConnectionPool

# store as Any internally to avoid generic-invariance issues from the library's
# types; cast on return to preserve the public API type for callers.
_pool: Any = None


async def init_db_pool() -> None:
    global _pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not set")
    pool = AsyncConnectionPool(database_url, min_size=1, max_size=5, open=False)
    await pool.open()
    _pool = pool


def get_db_pool() -> AsyncConnectionPool | None:
    pool = _pool
    if not isinstance(pool, AsyncConnectionPool):
        return None
    # pool is already the correct public type for callers, return it directly
    return pool


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
