from fastapi import FastAPI

app = FastAPI(title="order-service")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "order-service"}


@app.get("/")
async def root():
    return {"message": "order-service running"}
