import asyncio
import os

import bcrypt  # type: ignore[import]
import structlog  # type: ignore[import]
from psycopg_pool import AsyncConnectionPool  # type: ignore

logger = structlog.get_logger()


async def ensure_admin() -> None:
    """Idempotently ensure an admin user exists using ADMIN_USERNAME and ADMIN_PASSWORD env vars.

    This function is safe to call on startup multiple times.
    """
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    database_url = os.getenv("DATABASE_URL")

    if not admin_user or not admin_pass:
        logger.info(
            "admin-bootstrap.skipped",
            reason="missing-env",
            ADMIN_USERNAME=bool(admin_user),
        )
        return

    if not database_url:
        logger.warning("admin-bootstrap.no-db-url", reason="missing DATABASE_URL")
        return

    # Hash password in threadpool to avoid blocking the event loop
    try:

        def hashpw_lambda(pw: bytes) -> bytes:
            return bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12))

        hashed: bytes = await asyncio.to_thread(
            hashpw_lambda, admin_pass.encode("utf-8")
        )
        password_hash: str = hashed.decode("utf-8")
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("admin-bootstrap.hash-failed", error=str(exc))
        return

    pool = AsyncConnectionPool(database_url, min_size=1, max_size=5, open=False)  # type: ignore[no-untyped-call,unknown-member,unknown-variable]
    await pool.open()  # type: ignore[unknown-member,unknown-variable]
    try:
        async with pool.connection() as conn:  # type: ignore[unknown-member,unknown-variable]
            async with conn.cursor() as cur:  # type: ignore[unknown-member,unknown-variable]
                await cur.execute(  # type: ignore[unknown-member,unknown-variable]
                    "SELECT id FROM users WHERE username = %s", (admin_user,)
                )
                row = await cur.fetchone()  # type: ignore[unknown-member,unknown-variable]
                if row:
                    logger.info("admin-bootstrap.exists", username=admin_user)
                    return

                await cur.execute(  # type: ignore[unknown-member,unknown-variable]
                    "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, TRUE)",
                    (admin_user, password_hash),
                )
                logger.info("admin-bootstrap.created", username=admin_user)
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.exception("admin-bootstrap.failed", error=str(exc))
    finally:
        await pool.close()  # type: ignore[unknown-member,unknown-variable]
