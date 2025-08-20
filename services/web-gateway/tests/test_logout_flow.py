from fastapi.testclient import TestClient
from app.main import app
import httpx


def test_gateway_logout_clears_cookies_and_revokes(monkeypatch):
    # Fake auth-service behavior via AsyncClient stub
    class DummyResp:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self._json = json_data or {}

        def json(self):
            return self._json

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, headers=None):
            self.calls.append(("post", url, json, headers))
            if url.endswith("/token"):
                return DummyResp(200, {"access_token": "tok-access", "refresh_token": "tok-refresh"})
            if url.endswith("/logout"):
                return DummyResp(200, {"message": "logged out"})
            return DummyResp(404)

        async def get(self, url, headers=None):
            self.calls.append(("get", url, None, headers))
            return DummyResp(200, [])

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = TestClient(app)

    # register/login -> will set cookies
    r = client.post("/register", json={"username": "u1", "password": "p"})
    assert r.status_code in (200, 201)

    r = client.post("/login", json={"username": "u1", "password": "p"}, follow_redirects=False)
    assert r.status_code == 303
    # refresh_token stored as cookie
    assert client.cookies.get("refresh_token") == "tok-refresh"

    # call logout which should clear cookies and forward logout to auth
    r = client.post("/logout", follow_redirects=False)
    assert r.status_code == 303
    assert client.cookies.get("access_token") is None
    assert client.cookies.get("refresh_token") is None
    assert client.cookies.get("csrf_token") is None
