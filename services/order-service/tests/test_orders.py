from fastapi import FastAPI
from httpx import AsyncClient

# When tests are run from inside services/order-service, the package is importable as `app`
from app.orders import router as orders_router  # noqa: E402

app = FastAPI()
app.include_router(orders_router)


async def test_create_order(monkeypatch):
    class DummyConn:
        async def fetchrow(self, *args, **kwargs):
            return {"id": "order-123"}

    class DummyAcquireCM:
        async def __aenter__(self):
            return DummyConn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DummyPool:
        def acquire(self):
            return DummyAcquireCM()

    def dummy_get_db_pool():
        return DummyPool()

    # patch the get_db_pool used by the app.orders module
    monkeypatch.setattr("app.orders.get_db_pool", dummy_get_db_pool)

    # patch authentication dependency to return a fake user
    monkeypatch.setattr(
        "app.orders.get_current_user",
        lambda: {"sub": "u1", "username": "tester", "is_admin": False},
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post(
            "/orders/", json={"user_id": "u1", "item_name": "widget", "quantity": 2}
        )
        assert r.status_code == 201
        assert r.json()["id"] == "order-123"


async def test_admin_approve_reject(monkeypatch):
    class DummyConn:
        async def fetchrow(self, *args, **kwargs):
            # emulate returning id on update
            return {"id": "order-123"}

    class DummyAcquireCM:
        async def __aenter__(self):
            return DummyConn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DummyPool:
        def acquire(self):
            return DummyAcquireCM()

    def dummy_get_db_pool():
        return DummyPool()

    monkeypatch.setattr("app.orders.get_db_pool", dummy_get_db_pool)
    # admin user
    monkeypatch.setattr(
        "app.orders.get_current_user", lambda: {"sub": "admin", "username": "admin", "is_admin": True}
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/orders/order-123/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "APPROVED"

        r = await ac.post("/orders/order-123/reject")
        assert r.status_code == 200
        assert r.json()["status"] == "REJECTED"
