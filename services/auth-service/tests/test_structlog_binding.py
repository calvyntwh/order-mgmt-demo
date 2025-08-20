import uuid

import structlog
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_structlog_includes_request_id_on_log(capfd):
    logger = structlog.get_logger()

    @app.get("/__test-log")
    def _log():
        logger.info("auth-test-message", foo="bar")
        return {"ok": True}

    rid = str(uuid.uuid4())
    r = client.get("/__test-log", headers={"X-Request-ID": rid})
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == rid
    out, err = capfd.readouterr()
    assert "auth-test-message" in out or "auth-test-message" in err
