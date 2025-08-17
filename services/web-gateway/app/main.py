from fastapi import FastAPI

app = FastAPI(title="web-gateway")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "web-gateway"}


@app.get("/")
async def root():
    return {"message": "web-gateway running"}
