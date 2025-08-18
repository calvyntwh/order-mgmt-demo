import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import router as routes_router

app = FastAPI()
app.include_router(routes_router)


def test_whoami(monkeypatch):
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

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = TestClient(app)
    r = client.get("/whoami", headers={"Authorization": "Bearer fake"})
    if r.status_code != 200:
        raise AssertionError(f"Expected status 200, got {r.status_code}")
    data = r.json()
    if data["username"] != "tester":
        raise AssertionError(f"Expected username 'tester', got {data['username']}")
