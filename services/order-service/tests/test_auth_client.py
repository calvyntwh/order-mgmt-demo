import httpx
import pytest

from app import auth_client


@pytest.mark.asyncio
async def test_introspect_token(monkeypatch):
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

    res = await auth_client.introspect_token("fake-token")
    if res["username"] != "tester":
        raise AssertionError(f"Expected username 'tester', got {res['username']}")
    if res["is_admin"] is not False:
        raise AssertionError(f"Expected is_admin False, got {res['is_admin']}")
