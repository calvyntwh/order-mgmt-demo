from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from .auth import router as auth_router
from .observability import request_id_middleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging early so startup errors are captured in structured logs
    setup_logging()

    try:
        # Validate critical runtime settings early
        from .settings import settings as _settings

        _settings.validate()

        from .bootstrap import ensure_admin
        from .db import init_db_pool

        await init_db_pool()
        await ensure_admin()
    except Exception:
        # Use structured logging so startup errors include request/context info
        structlog.get_logger().exception("Error during startup")
        # re-raise so failing startup is visible to supervisors/CI
        raise
    yield
    try:
        from .db import close_db_pool

        await close_db_pool()
    except Exception:
        structlog.get_logger().exception("Error during shutdown")


app = FastAPI(title="auth-service", lifespan=lifespan)
app.middleware("http")(request_id_middleware)
app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth-service"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "auth-service running"}
