import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_request_id_echo_on_health():
    rid = str(uuid.uuid4())
    r = client.get("/health", headers={"X-Request-ID": rid})
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == rid


def test_request_id_on_error_response():
    @app.get("/__test-raise")
    def _raise():
        raise RuntimeError("intentional")

    rid = str(uuid.uuid4())
    r = client.get("/__test-raise", headers={"X-Request-ID": rid})
    assert r.status_code == 500
    assert r.headers.get("X-Request-ID") == rid
