from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.orders import get_current_user

# Keep tests isolated: override dependencies per-test
client = TestClient(app)

# Stable UUID used by other order tests
TEST_ORDER_ID = "11111111-1111-1111-1111-111111111111"


def _dummy_pool_for_get_order():
    class DummyConn:
        async def fetchrow(
            self, sql: str, *args: Any, **kwargs: Any
        ) -> dict[str, Any] | None:
            # Return an order owned by user 'u2' so a request from 'u1' should be forbidden
            if "SELECT id, user_id" in sql:
                return {
                    "id": TEST_ORDER_ID,
                    "user_id": "u2",
                    "item_name": "x",
                    "quantity": 1,
                }
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


def _dummy_pool_for_list_user():
    class DummyConn:
        async def fetchall(
            self, sql: str, *args: Any, **kwargs: Any
        ) -> list[dict[str, Any]]:
            # Return a single order for user 'u2'
            return [
                {"id": TEST_ORDER_ID, "user_id": "u2", "item_name": "x", "quantity": 1}
            ]

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


def test_list_user_orders_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-admin users should not be able to list another user's orders."""
    monkeypatch.setattr("app.orders.get_db_pool", _dummy_pool_for_list_user())

    def fake_user_nonadmin() -> dict[str, Any]:
        return {"sub": "u1", "username": "tester", "is_admin": False}

    orig = app.dependency_overrides.copy()
    try:
        app.dependency_overrides = {}
        app.dependency_overrides[get_current_user] = fake_user_nonadmin

        r = client.get("/orders/user/u2")
        if r.status_code != 403:
            raise AssertionError(
                f"Expected status 403 for forbidden, got {r.status_code}"
            )
    finally:
        app.dependency_overrides = orig


def test_get_order_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """Users should not be able to fetch an order they don't own unless admin."""
    monkeypatch.setattr("app.orders.get_db_pool", _dummy_pool_for_get_order())

    def fake_user_nonadmin() -> dict[str, Any]:
        return {"sub": "u1", "username": "tester", "is_admin": False}

    orig = app.dependency_overrides.copy()
    try:
        app.dependency_overrides = {}
        app.dependency_overrides[get_current_user] = fake_user_nonadmin

        r = client.get(f"/orders/{TEST_ORDER_ID}")
        if r.status_code != 403:
            raise AssertionError(
                f"Expected status 403 for forbidden order fetch, got {r.status_code}"
            )
    finally:
        app.dependency_overrides = orig
