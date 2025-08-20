from typing import Any

import httpx
from fastapi.testclient import TestClient

from app.main import app


class DummyResponse:
    def __init__(self, data: Any, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._data


class DummyClient:
    def __init__(self, seen: dict[str, Any] | None = None):
        self._seen = seen or {}

    async def __aenter__(self) -> "DummyClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False

    async def post(
        self, url: str, json: Any | None = None, headers: dict[str, str] | None = None
    ) -> DummyResponse:
        # token exchange endpoint (auth-service)
        if url.endswith("/token"):
            return DummyResponse({"access_token": "fake-token"}, status_code=200)
        # order creation endpoint
        if url.endswith("/orders/") or "/approve" in url or "/reject" in url:
            return DummyResponse({"id": "o-created"}, status_code=201)
        return DummyResponse({}, status_code=200)

    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> DummyResponse:
        # orders fetch
        if url.endswith("/orders/me") or url.endswith("/me"):
            return DummyResponse([{"id": "o1", "item_name": "x"}], status_code=200)
        if url.endswith("/orders/admin"):
            return DummyResponse([{"id": "a1"}], status_code=200)
        return DummyResponse([], status_code=200)


def test_login_sets_secure_cookie_when_env_production(monkeypatch):
    # Ensure ENV=production results in Secure flag on set-cookie
    monkeypatch.setenv("ENV", "production")

    def _make_client(*args: Any, **kwargs: Any) -> DummyClient:
        return DummyClient()

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    client = TestClient(app)
    # Don't follow the redirect so we can inspect Set-Cookie headers on the response
    r = client.post(
        "/login", json={"username": "u", "password": "p"}, follow_redirects=False
    )
    assert r.status_code in (302, 303)
    set_cookie = r.headers.get("set-cookie", "")
    # at least one cookie should include Secure when ENV=production
    assert "Secure" in set_cookie
    # access_token cookie should be HttpOnly
    assert "access_token" in set_cookie
    assert "HttpOnly" in set_cookie


def test_submit_order_rejects_missing_csrf(monkeypatch):
    def _make_client(*args: Any, **kwargs: Any) -> DummyClient:
        return DummyClient()

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    client = TestClient(app)
    # set only access_token cookie (no csrf_token)
    client.cookies.set("access_token", "raw-token")

    r = client.post(
        "/order",
        data={"item_name": "x", "quantity": "1"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 403
    assert "CSRF verification failed" in r.text


def test_submit_order_allows_with_csrf(monkeypatch):
    def _make_client(*args: Any, **kwargs: Any) -> DummyClient:
        return DummyClient()

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    client = TestClient(app)
    # set both access_token and csrf_token cookies and provide csrf in form
    client.cookies.set("access_token", "raw-token")
    client.cookies.set("csrf_token", "tok-csrf")

    r = client.post(
        "/order",
        data={"item_name": "x", "quantity": "1", "csrf_token": "tok-csrf"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    assert "Order created successfully" in r.text
