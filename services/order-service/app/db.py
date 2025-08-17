import os
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.pool.Pool] = None


async def init_db_pool() -> None:
    global _pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not set")
    _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)


def get_db_pool() -> asyncpg.pool.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
