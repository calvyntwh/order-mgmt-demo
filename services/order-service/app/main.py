from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import close_db_pool, init_db_pool
from .observability import request_id_middleware, setup_logging
from .orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    # mark ready after init
    app.state.ready = True
    yield
    await close_db_pool()


setup_logging()
app = FastAPI(title="order-service", lifespan=lifespan)
app.middleware("http")(request_id_middleware)
app.include_router(orders_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "order-service"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    if getattr(app.state, "ready", False):
        return {"status": "ready", "service": "order-service"}
    from fastapi.responses import JSONResponse

    return JSONResponse(
        {"status": "not ready", "service": "order-service"}, status_code=503
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "order-service running"}
