import threading
import time
import uuid
from typing import Dict, Any

import pytest

from app import session_store


class DummyResponse:
    def __init__(self, status_code: int, json_data: Dict[str, Any] | None = None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class DummySession:
    """A tiny in-memory Valkey-like server over a requests-like Session API.

    Supports:
      POST /sessions -> {refresh_token, session, ttl}
      POST /sessions/rotate -> {old_token, ttl} -> returns {new_token} or 404
      POST /sessions/revoke -> {token}
      GET /sessions/{token} -> returns 200+{session} or 404
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def post(
        self, url: str, json: Dict[str, Any] | None = None, timeout: int | None = None
    ):
        path = url.split("//", 1)[-1].split("/", 1)[-1]
        if path == "sessions":
            token = json["refresh_token"]
            self._store[token] = {
                "session": json["session"],
                "expires_at": time.time() + json.get("ttl", 0),
            }
            return DummyResponse(200, {})
        if path == "sessions/rotate":
            old = json["old_token"]
            ttl = json.get("ttl", 0)
            with self._lock:
                rec = self._store.get(old)
                if not rec:
                    return DummyResponse(404)
                # rotate: remove old, add new with same session
                new = uuid.uuid4().hex
                self._store.pop(old, None)
                self._store[new] = {
                    "session": rec["session"],
                    "expires_at": time.time() + ttl,
                }
                return DummyResponse(200, {"new_token": new})
        if path == "sessions/revoke":
            tok = json["token"]
            with self._lock:
                self._store.pop(tok, None)
            return DummyResponse(200, {})
        return DummyResponse(404)

    def get(self, url: str, timeout: int | None = None):
        path = url.split("//", 1)[-1].split("/", 1)[-1]
        if path.startswith("sessions/"):
            token = path.split("/", 1)[1]
            rec = self._store.get(token)
            if not rec:
                return DummyResponse(404)
            # check expiry
            if rec.get("expires_at") and rec["expires_at"] < time.time():
                with self._lock:
                    self._store.pop(token, None)
                return DummyResponse(404)
            return DummyResponse(200, {"session": rec["session"]})
        return DummyResponse(404)


@pytest.fixture(autouse=True)
def patch_requests_session(monkeypatch):
    """Monkeypatch session_store.requests.Session to our DummySession for tests."""
    # session_store uses httpx.Client for Valkey calls; patch that to our DummySession
    monkeypatch.setattr(session_store.httpx, "Client", DummySession)
    yield


def test_valkey_store_rotate_and_revoke():
    store = session_store.ValkeySessionStore("http://valkey")
    t = "r1"
    session = {"sub": "u1", "username": "u1", "is_admin": False}
    store.store_refresh_token(t, session, ttl_seconds=60)

    # verify stored
    got = store.get_session(t)
    assert got == session

    # rotate
    new = store.rotate_refresh_token(t, ttl_seconds=60)
    assert new is not None
    assert new != t

    # old should be gone
    assert store.get_session(t) is None
    assert store.get_session(new) == session

    # revoke
    store.revoke_refresh_token(new)
    assert store.is_refresh_revoked(new)
    assert store.get_session(new) is None


def test_valkey_concurrent_rotate():
    store = session_store.ValkeySessionStore("http://valkey")
    initial = "r_conc"
    session = {"sub": "u2", "username": "u2", "is_admin": False}
    store.store_refresh_token(initial, session, ttl_seconds=60)

    results = []

    def attempt_rotate():
        res = store.rotate_refresh_token(initial, ttl_seconds=60)
        results.append(res)

    threads = [threading.Thread(target=attempt_rotate) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # exactly one should succeed (non-None)
    successes = [r for r in results if r]
    assert len(successes) == 1
    new_tok = successes[0]
    assert store.get_session(new_tok) == session
