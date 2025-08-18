from fastapi import FastAPI
from httpx import AsyncClient

from app.routes import router as routes_router

app = FastAPI()
app.include_router(routes_router)


async def test_whoami(monkeypatch):
    # Dummy response from auth proxy
    class DummyResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self._data

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            return DummyResponse({"sub": "u1", "username": "tester", "is_admin": False})

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/whoami", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200
        body = r.json()
        assert body["username"] == "tester"
