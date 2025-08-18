import os

from psycopg import AsyncConnection  # type: ignore
from psycopg_pool import AsyncConnectionPool  # type: ignore

_pool: AsyncConnectionPool[AsyncConnection] | None = None  # type: ignore[reportUnknownVariableType]


async def init_db_pool() -> None:
    global _pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not set")
    pool = AsyncConnectionPool(database_url, min_size=1, max_size=5, open=False)
    await pool.open()  # type: ignore[reportUnknownMemberType]
    _pool = pool


def get_db_pool() -> AsyncConnectionPool[AsyncConnection] | None:
    pool = _pool
    if not isinstance(pool, AsyncConnectionPool):
        return None
    if hasattr(pool, "open") and getattr(pool, "open", False):  # type: ignore[reportUnknownMemberType]
        return pool  # type: ignore[reportUnknownVariableType]
    return None  # type: ignore[reportUnknownParameterType]


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()  # type: ignore[reportUnknownMemberType]
        _pool = None
