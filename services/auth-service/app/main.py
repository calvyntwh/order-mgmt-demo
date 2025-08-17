from fastapi import FastAPI

app = FastAPI(title="auth-service")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service"}


@app.get("/")
async def root():
    return {"message": "auth-service running"}
