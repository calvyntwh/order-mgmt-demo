from contextlib import asynccontextmanager
from fastapi import FastAPI

from .auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from .bootstrap import ensure_admin
        from .db import init_db_pool

        await init_db_pool()
        await ensure_admin()
    except Exception:
        pass
    yield
    try:
        from .db import close_db_pool

        await close_db_pool()
    except Exception:
        pass


app = FastAPI(title="auth-service", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth-service"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "auth-service running"}
