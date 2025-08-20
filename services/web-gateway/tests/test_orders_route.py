from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_types import MonkeyPatch

from app.routes import router as routes_router

app = FastAPI()
app.include_router(routes_router)


class DummyResponse:
    def __init__(self, data: Any, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._data


class DummyClient:
    def __init__(self, seen: dict[str, Any]):
        self._seen = seen

    async def __aenter__(self) -> "DummyClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False

    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> DummyResponse:
        # record the observed url and headers so the test can assert on them
        self._seen["url"] = url
        self._seen["headers"] = dict(headers or {})
        return DummyResponse([{"id": "o1", "item_name": "x"}], status_code=200)


def test_list_orders_uses_orders_me(monkeypatch: MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def _make_client(*args: Any, **kwargs: Any) -> DummyClient:
        return DummyClient(seen)

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    client = TestClient(app)
    # provide an Authorization header and ensure the gateway forwards it
    r = client.get("/orders", headers={"Authorization": "Bearer token-123"})
    assert r.status_code == 200
    assert seen.get("url") is not None and seen["url"].endswith("/orders/me")
    assert seen.get("headers", {}).get("Authorization") == "Bearer token-123"


def test_list_orders_forwards_cookie_token(monkeypatch: MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def _make_client(*args: Any, **kwargs: Any) -> DummyClient:
        return DummyClient(seen)

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    client = TestClient(app)
    # provide access_token cookie and expect gateway to prefix with Bearer
    r = client.get("/orders", cookies={"access_token": "raw-token"})
    assert r.status_code == 200
    assert seen.get("url") is not None and seen["url"].endswith("/orders/me")
    assert seen.get("headers", {}).get("Authorization") == "Bearer raw-token"
