import pytest
import threading
from fastapi.testclient import TestClient

from app.main import app


# Minimal fake DB pool used for tests. Mirrors the async context manager
# protocol used by the real psycopg_pool.AsyncConnectionPool in a small way.
class FakeCursor:
    def __init__(self, pool: "FakePool") -> None:
        self.pool = pool
        self._last = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query: str, *params):
        # support two queries used by tests: SELECT id FROM users WHERE username
        # and INSERT INTO users (username, password_hash)
        q = query.strip().upper()

        # helper: psycopg/psycopg_pool often passes parameters as a single tuple
        # (e.g. execute(query, (val,))). Normalize to the actual values.
        def _first_param(params):
            if len(params) == 1 and isinstance(params[0], (list, tuple)):
                return params[0][0]
            return params[0]

        if q.startswith("SELECT ID FROM USERS"):
            username = _first_param(params)
            user = self.pool.users.get(username)
            if user:
                self._last = (user["id"],)
            else:
                self._last = None
        elif q.startswith("SELECT ID, PASSWORD_HASH, IS_ADMIN FROM USERS"):
            username = _first_param(params)
            user = self.pool.users.get(username)
            if user:
                self._last = (user["id"], user["password_hash"], user["is_admin"])
            else:
                self._last = None
        elif q.startswith("INSERT INTO USERS"):
            # psycopg_pool passes params as a single tuple, so handle both cases
            p = (
                params[0]
                if len(params) == 1 and isinstance(params[0], (list, tuple))
                else params
            )
            username, password_hash = p
            uid = str(self.pool.next_id)
            self.pool.next_id += 1
            self.pool.users[username] = {
                "id": uid,
                "password_hash": password_hash,
                "is_admin": False,
            }
            self._last = None
        else:
            self._last = None

    async def fetchone(self):
        return self._last


class FakeConn:
    def __init__(self, pool: "FakePool") -> None:
        self.pool = pool

    def cursor(self):
        return FakeCursor(self.pool)


class FakePool:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}
        self.next_id = 1

    class _ConnCtx:
        def __init__(self, conn: FakeConn):
            self._conn = conn

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def connection(self):
        return FakePool._ConnCtx(FakeConn(self))


def create_user_and_get_tokens(client: TestClient, username: str = "u1") -> dict:
    # register
    client.post("/register", json={"username": username, "password": "p"})
    # token
    r = client.post("/token", json={"username": username, "password": "p"})
    assert r.status_code == 200
    return r.json()


def test_refresh_rotates_and_invalidates_old_token():
    fake = FakePool()
    # inject fake pool into auth module
    import app.auth as auth_mod

    auth_mod.get_db_pool = lambda: fake
    client = TestClient(app)

    tokens = create_user_and_get_tokens(client)
    old_refresh = tokens["refresh_token"]

    # rotate once
    r = client.post("/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new = r.json()["refresh_token"]

    # old refresh should now be invalid
    r2 = client.post("/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401

    # new refresh should work
    r3 = client.post("/refresh", json={"refresh_token": new})
    assert r3.status_code == 200


def test_concurrent_refresh_only_one_succeeds():
    fake = FakePool()
    import app.auth as auth_mod

    auth_mod.get_db_pool = lambda: fake
    client = TestClient(app)
    tokens = create_user_and_get_tokens(client, username="raceuser")
    refresh = tokens["refresh_token"]

    results = []

    def do_refresh():
        r = client.post("/refresh", json={"refresh_token": refresh})
        results.append(r.status_code)

    threads = [threading.Thread(target=do_refresh) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one should succeed (200) and the other should fail (401)
    assert sorted(results) == [200, 401]
