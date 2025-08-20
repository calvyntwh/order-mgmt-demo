import json
import uuid
import importlib.util
from pathlib import Path

import pytest


class DummyPipeline:
    def __init__(self, client):
        self.client = client
        self.ops = []

    def set(self, k, v):
        self.ops.append(("set", k, v))
        return self

    def expire(self, k, t):
        self.ops.append(("expire", k, t))
        return self

    def delete(self, k):
        self.ops.append(("delete", k))
        return self

    def execute(self):
        for op in self.ops:
            if op[0] == "set":
                _, k, v = op
                self.client.store[k] = v
            elif op[0] == "expire":
                # noop for dummy
                pass
            elif op[0] == "delete":
                _, k = op
                self.client.store.pop(k, None)


class DummyValkeyClient:
    def __init__(self, host="localhost", port=6379, db=0, decode_responses=False):
        self.store = {}

    def set(self, k, v):
        self.store[k] = v

    def get(self, k):
        return self.store.get(k)

    def expire(self, k, ttl):
        # noop in dummy
        return True

    def delete(self, k):
        self.store.pop(k, None)

    def pipeline(self):
        return DummyPipeline(self)


@pytest.fixture(autouse=True)
def patch_valkey_module(monkeypatch):
    # Import via package path so pytest's PYTHONPATH resolution is used.
    import app.session_store as session_store_mod

    fake_mod = type("fake", (), {})
    fake_mod.Valkey = DummyValkeyClient
    monkeypatch.setattr(session_store_mod, "valkey", fake_mod, raising=False)
    yield


def make_store():
    import app.session_store as session_store_mod

    return session_store_mod.ValkeySessionStore("valkey://localhost:6379/0")


def test_store_and_get_session():
    s = make_store()
    token = "t1"
    data = {"user_id": 1}
    s.store_refresh_token(token, data, ttl_seconds=60)
    got = s.get_session(token)
    assert got == data


def test_is_refresh_revoked_and_revoke():
    s = make_store()
    token = "t2"
    assert s.is_refresh_revoked(token) is True
    s.store_refresh_token(token, {"user_id": 2}, ttl_seconds=60)
    assert s.is_refresh_revoked(token) is False
    s.revoke_refresh_token(token)
    assert s.is_refresh_revoked(token) is True


def test_rotate_refresh_token():
    s = make_store()
    old = "oldtok"
    s.store_refresh_token(old, {"user_id": 3}, ttl_seconds=60)
    new = s.rotate_refresh_token(old, ttl_seconds=120)
    assert new is not None and new != old
    # old should be gone
    assert s.get_session(old) is None
    # new should exist
    assert s.get_session(new) == {"user_id": 3}
