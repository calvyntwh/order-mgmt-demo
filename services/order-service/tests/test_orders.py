from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.orders import get_current_user, require_admin


# Dependency overrides for tests
def fake_user() -> dict[str, Any]:
    return {"sub": "u1", "username": "tester", "is_admin": True}


def fake_admin() -> dict[str, Any]:
    return {"sub": "admin", "username": "admin", "is_admin": True}


app.dependency_overrides = {}
app.dependency_overrides[get_current_user] = fake_user
app.dependency_overrides[require_admin] = fake_admin

client = TestClient(app)

# Use a stable UUID string for tests
TEST_ORDER_ID = "11111111-1111-1111-1111-111111111111"


def test_create_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.orders.get_db_pool", _dummy_get_db_pool())
    headers = {"Authorization": "Bearer test-token"}
    r = client.post(
        "/orders/",
        json={"user_id": "u1", "item_name": "widget", "quantity": 2},
        headers=headers,
    )
    if r.status_code != 201:
        raise AssertionError(f"Expected status 201, got {r.status_code}")
    if r.json()["id"] != TEST_ORDER_ID:
        raise AssertionError(f"Expected id '{TEST_ORDER_ID}', got {r.json()['id']}")


def test_admin_approve_reject(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.orders.get_db_pool", _dummy_get_db_pool(approve_only=True))
    headers = {"Authorization": "Bearer test-token"}
    r = client.post(f"/orders/{TEST_ORDER_ID}/approve", headers=headers)
    if r.status_code != 200:
        raise AssertionError(f"Expected status 200, got {r.status_code}")
    if r.json()["status"] != "APPROVED":
        raise AssertionError(f"Expected status 'APPROVED', got {r.json()['status']}")

    r = client.post(f"/orders/{TEST_ORDER_ID}/reject", headers=headers)
    if r.status_code != 200:
        raise AssertionError(f"Expected status 200, got {r.status_code}")
    if r.json()["status"] != "REJECTED":
        raise AssertionError(f"Expected status 'REJECTED', got {r.json()['status']}")


def _dummy_get_db_pool(approve_only: bool = False):
    class DummyConn:
        async def fetchrow(
            self, sql: str, *args: Any, **kwargs: Any
        ) -> dict[str, object] | None:
            # Use `in` checks against the SQL string; we keep `sql` typed as str
            # and *args/**kwargs as Any so the typechecker doesn't complain.
            if not approve_only and "INSERT INTO orders" in sql:
                return {"id": TEST_ORDER_ID}
            if "UPDATE orders SET status = 'APPROVED'" in sql:
                return {"id": TEST_ORDER_ID, "status": "APPROVED"}
            if "UPDATE orders SET status = 'REJECTED'" in sql:
                return {"id": TEST_ORDER_ID, "status": "REJECTED"}
            return None

    class DummyAcquireCM:
        async def __aenter__(self) -> DummyConn:
            return DummyConn()

        async def __aexit__(
            self, exc_type: type | None, exc: BaseException | None, tb: object | None
        ) -> bool:
            return False

    class DummyPool:
        def acquire(self):
            return DummyAcquireCM()

    return DummyPool()
