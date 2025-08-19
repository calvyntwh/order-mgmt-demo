from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import router as routes_router

app = FastAPI()
app.include_router(routes_router)


def test_whoami(monkeypatch: Any) -> None:
    # Dummy response from auth proxy
    class DummyResponse:
        def __init__(self, data: dict[str, object]) -> None:
            self._data = data

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._data

    class DummyClient:
        async def __aenter__(self) -> "DummyClient":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
            return False

        async def get(self, *args: Any, **kwargs: Any) -> DummyResponse:
            return DummyResponse({"sub": "u1", "username": "tester", "is_admin": False})

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = TestClient(app)
    r = client.get("/whoami", headers={"Authorization": "Bearer fake"})
    if r.status_code != 200:
        raise AssertionError(f"Expected status 200, got {r.status_code}")
    data = r.json()
    if data["username"] != "tester":
        raise AssertionError(f"Expected username 'tester', got {data['username']}")
