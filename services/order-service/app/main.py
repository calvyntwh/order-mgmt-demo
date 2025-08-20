from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import close_db_pool, init_db_pool
from .orders import router as orders_router
from .observability import setup_logging, request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()


setup_logging()
app = FastAPI(title="order-service", lifespan=lifespan)
app.middleware("http")(request_id_middleware)
app.include_router(orders_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "order-service"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "order-service running"}
