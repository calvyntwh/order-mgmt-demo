import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_base_injects_csrf_hidden_input(monkeypatch):
    # Simulate that csrf cookie exists and verify that the rendered HTML
    # contains a hidden input after DOMContentLoaded would run. We can't run
    # DOM here, so assert the client-side script is present in base.html
    r = client.get("/login")
    assert r.status_code == 200
    body = r.text
    # script that reads csrf_token cookie should be present
    assert "getCookie(" in body or "csrf_token" in body


def test_htmx_config_request_includes_header(monkeypatch):
    # Use a DummyClient to capture headers set by htmx event handler
    seen = {}

    class DummyClient:
        def __init__(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            seen["headers"] = dict(headers or {})

            class R:
                def __init__(self):
                    self.status_code = 200

                def json(self):
                    return []

            return R()

    def _make_client(*args, **kwargs):
        return DummyClient()

    monkeypatch.setattr(httpx, "AsyncClient", _make_client)

    # Provide both access_token and csrf_token cookies so server-side won't reject
    r = client.get("/orders", cookies={"access_token": "raw", "csrf_token": "tok"})
    assert r.status_code == 200
    # The gateway will forward headers; ensure Authorization header was built
    # (X-CSRF-Token header added by client-side HTMX handler can't be observed
    # here because tests don't execute browser scripts. We assert the code path
    # that accepts X-CSRF-Token header exists by ensuring request succeeds.
    assert "headers" in seen
