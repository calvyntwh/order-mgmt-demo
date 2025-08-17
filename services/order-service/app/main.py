from fastapi import FastAPI

from .db import close_db_pool, init_db_pool
from .orders import router as orders_router

app = FastAPI(title="order-service")


@app.on_event("startup")
async def startup_event():
    await init_db_pool()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db_pool()


app.include_router(orders_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "order-service"}


@app.get("/")
async def root():
    return {"message": "order-service running"}
