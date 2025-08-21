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


class DummyAdminClient:
    def __init__(self, responses: dict[str, Any]) -> None:
        # responses keyed by (method, path) tuples as strings like 'GET /orders/1'
        self._responses = responses

    async def __aenter__(self) -> "DummyAdminClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def get(self, url: str, headers: dict | None = None) -> DummyResponse:
        # keep only path for matching
        path = url.replace("http://order-service:8002", "")
        key = f"GET {path}"
        data = self._responses.get(key, [])
        return DummyResponse(data)

    async def post(self, url: str, headers: dict | None = None) -> DummyResponse:
        path = url.replace("http://order-service:8002", "")
        key = f"POST {path}"
        return DummyResponse(self._responses.get(key, {}), status_code=204)


def make_admin_claims(is_admin: bool = True) -> dict[str, Any]:
    return {"sub": "admin", "username": "admin", "is_admin": is_admin}


def test_admin_approve_htmx(monkeypatch):
    # Simulate an admin approving order '1' via HTMX
    responses = {
        "POST /orders/1/approve": {},
        "GET /orders/1": {"id": 1, "status": "approved", "owner": "u1"},
    }

    def _make_client(*args, **kwargs):
        return DummyAdminClient(responses)

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    # monkeypatch current user to be admin
    async def _get_current_user(request):
        return make_admin_claims(True)

    monkeypatch.setattr("app.main.get_current_user_optional", _get_current_user)

    client = TestClient(app)
    headers = {"HX-Request": "true", "X-CSRF-Token": "tok"}
    # Provide csrf cookie to satisfy CSRF check
    r = client.post(
        "/admin/1/approve",
        headers=headers,
        cookies={"csrf_token": "tok", "access_token": "t"},
    )
    assert r.status_code == 200
    # fragment should include the order id and approved status
    assert "approved" in r.text


def test_admin_reject_htmx(monkeypatch):
    responses = {
        "POST /orders/2/reject": {},
        "GET /orders/2": {"id": 2, "status": "rejected", "owner": "u2"},
    }

    def _make_client(*args, **kwargs):
        return DummyAdminClient(responses)

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    async def _get_current_user(request):
        return make_admin_claims(True)

    monkeypatch.setattr("app.main.get_current_user_optional", _get_current_user)

    client = TestClient(app)
    headers = {"HX-Request": "true", "X-CSRF-Token": "tok"}
    r = client.post(
        "/admin/2/reject",
        headers=headers,
        cookies={"csrf_token": "tok", "access_token": "t"},
    )
    assert r.status_code == 200
    assert "rejected" in r.text


def test_admin_privilege_checks(monkeypatch):
    # non-admin should get a 403 with admin message
    async def _get_current_user_none(request):
        return None

    monkeypatch.setattr("app.main.get_current_user_optional", _get_current_user_none)
    client = TestClient(app)
    r = client.get("/admin")
    # Redirect to login (no claims) is implemented with 303
    assert r.status_code in (303, 200)

    async def _get_current_user_not_admin(request):
        return make_admin_claims(False)

    monkeypatch.setattr(
        "app.main.get_current_user_optional", _get_current_user_not_admin
    )
    r2 = client.get("/admin")
    assert r2.status_code == 403


def test_admin_list_error_and_empty(monkeypatch):
    # Error from order-service should render an error notification
    class DummyErrClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, headers: dict | None = None):
            # return a 500 for the admin list
            return DummyResponse([], status_code=500)

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: DummyErrClient())

    async def _get_current_user(request):
        return make_admin_claims(True)

    monkeypatch.setattr("app.main.get_current_user_optional", _get_current_user)
    client = TestClient(app)
    r = client.get("/admin")
    assert r.status_code == 200
    assert "Failed to fetch orders" in r.text

    # Empty list should show 'No orders found.'
    def _make_client_empty(*args, **kwargs):
        return DummyAdminClient({"GET /orders/admin": []})

    monkeypatch.setattr(httpx, "AsyncClient", _make_client_empty)
    r2 = client.get("/admin")
    assert r2.status_code == 200
    assert "No orders found." in r2.text


def test_admin_approve_reject_redirects(monkeypatch):
    # Non-HTMX flows should redirect back to /admin
    responses = {
        "POST /orders/10/approve": {},
        "POST /orders/11/reject": {},
    }

    def _make_client(*args, **kwargs):
        return DummyAdminClient(responses)

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    async def _get_current_user(request):
        return make_admin_claims(True)

    monkeypatch.setattr("app.main.get_current_user_optional", _get_current_user)
    client = TestClient(app)

    # Approve: no HX-Request header, include CSRF header+cookie, do not follow redirect
    r = client.post(
        "/admin/10/approve",
        headers={"X-CSRF-Token": "tok"},
        cookies={"csrf_token": "tok", "access_token": "t"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers.get("location") == "/admin"

    # Reject: similarly
    r2 = client.post(
        "/admin/11/reject",
        headers={"X-CSRF-Token": "tok"},
        cookies={"csrf_token": "tok", "access_token": "t"},
        follow_redirects=False,
    )
    assert r2.status_code == 303
    assert r2.headers.get("location") == "/admin"
