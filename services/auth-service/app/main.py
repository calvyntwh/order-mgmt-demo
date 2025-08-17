from fastapi import FastAPI

from .auth import router as auth_router

app = FastAPI(title="auth-service")


@app.on_event("startup")
async def startup_event():
    # Initialize DB pool and run admin bootstrap
    try:
        from .bootstrap import ensure_admin
        from .db import init_db_pool

        await init_db_pool()
        await ensure_admin()
    except Exception:
        # Tolerate missing env/deps in local dev
        pass


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from .db import close_db_pool

        await close_db_pool()
    except Exception:
        pass

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service"}


@app.get("/")
async def root():
    return {"message": "auth-service running"}
