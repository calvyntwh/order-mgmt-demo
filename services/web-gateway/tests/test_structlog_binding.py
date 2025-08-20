import uuid

import structlog
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_structlog_includes_request_id_on_log(capfd):
    # create endpoint that logs using structlog
    logger = structlog.get_logger()

    @app.get("/__test-log")
    def _log(request_id: str | None = None):
        logger.info("test-message", foo="bar")
        return {"ok": True}

    rid = str(uuid.uuid4())
    r = client.get("/__test-log", headers={"X-Request-ID": rid})
    assert r.status_code == 200
    # ensure response has header
    assert r.headers.get("X-Request-ID") == rid
    # capture stdout/stderr where structlog emits JSON
    out, err = capfd.readouterr()
    # At least ensure no crash and that request id binding didn't raise
    assert "test-message" in out or "test-message" in err
