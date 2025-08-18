import asyncio
import httpx

from app import auth_client


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
    assert res["username"] == "tester"
    assert res["is_admin"] is False


def test_run():
    asyncio.run(test_introspect_token(None))
