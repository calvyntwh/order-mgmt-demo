from contextlib import asynccontextmanager

from fastapi import FastAPI

from .auth import router as auth_router
from .observability import setup_logging, request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

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
    except Exception as e:
        logging.exception("Error during startup")
        # re-raise so failing startup is visible to supervisors/CI
        raise
    yield
    try:
        from .db import close_db_pool

        await close_db_pool()
    except Exception as e:
        logging.exception("Error during shutdown")


app = FastAPI(title="auth-service", lifespan=lifespan)
app.middleware("http")(request_id_middleware)
app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth-service"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "auth-service running"}
