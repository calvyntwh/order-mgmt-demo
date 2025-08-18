
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .db import close_db_pool, init_db_pool
from .orders import router as orders_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()

app = FastAPI(title="order-service", lifespan=lifespan)
app.include_router(orders_router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "order-service"}

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "order-service running"}
