from fastapi.testclient import TestClient

from app.main import app


class FakeCursor:
    def __init__(self, pool: "FakePool") -> None:
        self.pool = pool
        self._last = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query: str, *params):
        q = query.strip().upper()

        def _first_param(params):
            if len(params) == 1 and isinstance(params[0], list | tuple):
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
            p = (
                params[0]
                if len(params) == 1 and isinstance(params[0], list | tuple)
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
    client.post("/register", json={"username": username, "password": "p"})
    r = client.post("/token", json={"username": username, "password": "p"})
    assert r.status_code == 200
    return r.json()


def test_token_response_matches_declared_schema() -> None:
    fake = FakePool()
    import app.auth as auth_mod

    # Inject fake DB pool used by the auth module
    auth_mod.get_db_pool = lambda: fake

    client = TestClient(app)

    tokens = create_user_and_get_tokens(client)

    # Import the Pydantic response model and validate the received JSON
    from pydantic import ValidationError

    from app.auth import TokenWithRefresh

    try:
        # model_validate will raise on invalid data (pydantic v2)
        TokenWithRefresh.model_validate(tokens)
    except ValidationError as exc:
        raise AssertionError(f"/token response did not match TokenWithRefresh: {exc}")
