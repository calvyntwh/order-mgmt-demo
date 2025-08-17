import asyncio
import logging
import os
from typing import Optional

import asyncpg
import bcrypt
import structlog

logger = structlog.get_logger()


async def ensure_admin() -> None:
    """Idempotently ensure an admin user exists using ADMIN_USERNAME and ADMIN_PASSWORD env vars.

    This function is safe to call on startup multiple times.
    """
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    database_url = os.getenv("DATABASE_URL")

    if not admin_user or not admin_pass:
        logger.info("admin-bootstrap.skipped", reason="missing-env", ADMIN_USERNAME=bool(admin_user))
        return

    if not database_url:
        logger.warning("admin-bootstrap.no-db-url", reason="missing DATABASE_URL")
        return

    # Hash password in threadpool to avoid blocking the event loop
    try:
        hashed = await asyncio.to_thread(
            lambda pw: bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)),
            admin_pass.encode("utf-8"),
        )
        password_hash = hashed.decode("utf-8")
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("admin-bootstrap.hash-failed", error=str(exc))
        return

    conn: Optional[asyncpg.Connection] = None
    try:
        conn = await asyncpg.connect(database_url)
        row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", admin_user)
        if row:
            logger.info("admin-bootstrap.exists", username=admin_user)
            return

        await conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES ($1, $2, TRUE)",
            admin_user,
            password_hash,
        )
        logger.info("admin-bootstrap.created", username=admin_user)
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.exception("admin-bootstrap.failed", error=str(exc))
    finally:
        if conn is not None:
            await conn.close()
