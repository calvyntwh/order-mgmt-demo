import asyncio
import sys
import types
from collections.abc import Callable
from typing import Any

import pytest


class FakeConn:
    def __init__(self, exists: bool = False) -> None:
        self._exists: bool = exists
        self.executed: list[tuple[str, str, str]] = []

    async def fetchrow(self, query: str, username: str) -> dict[str, str] | None:
        if self._exists:
            return {"id": "some-uuid"}
        return None

    async def execute(self, query: str, username: str, password_hash: str) -> None:
        self.executed.append((query, username, password_hash))

    async def close(self) -> None:
        pass


class FakeAsyncPGModule(types.ModuleType):
    def __init__(self, exists: bool = False) -> None:
        super().__init__("asyncpg")
        self._exists: bool = exists

    async def connect(self, database_url: str) -> FakeConn:
        return FakeConn(exists=self._exists)


class FakePsycopgPool(types.ModuleType):
    """Minimal fake psycopg_pool exposing AsyncConnectionPool used by bootstrap.ensure_admin.

    The real AsyncConnectionPool can attempt network operations during open/connection; this
    fake keeps everything in-process and synchronous for tests.
    """

    def __init__(self, name: str, exists: bool = False) -> None:
        super().__init__(name)
        self._exists = exists

    class AsyncConnectionPool:
        def __init__(
            self,
            database_url: str,
            min_size: int = 1,
            max_size: int = 5,
            open: bool = False,
        ):
            self._database_url = database_url

        async def open(self) -> None:  # pragma: no cover - trivial fake
            return None

        async def close(self) -> None:  # pragma: no cover - trivial fake
            return None

        # Async context manager for connection()
        class _ConnCtx:
            def __init__(self, conn: FakeConn):
                self._conn = conn

            async def __aenter__(self) -> FakeConn:
                return self._conn

            async def __aexit__(
                self,
                exc_type: type | None,
                exc: BaseException | None,
                tb: object | None,
            ) -> bool:
                return False

        def connection(self):
            # Use the exists flag from the outer FakePsycopgPool class if present.
            # The class object itself doesn't carry instance state here, so read
            # from the module-level object that will be registered in sys.modules.
            mod = sys.modules.get("psycopg_pool")
            exists = False
            if mod is not None and hasattr(mod, "_exists"):
                exists = getattr(mod, "_exists")
            return FakePsycopgPool.AsyncConnectionPool._ConnCtx(FakeConn(exists=exists))


def _import_with_fakes(exists: bool = False):
    # Insert fake asyncpg module into sys.modules before importing
    fake = FakeAsyncPGModule(exists=exists)
    # Force-replace any real asyncpg with our fake so psycopg_pool uses it.
    sys.modules["asyncpg"] = fake

    # Insert fake psycopg_pool module so bootstrap imports the fake AsyncConnectionPool
    fake_pool = FakePsycopgPool("psycopg_pool", exists=exists)
    sys.modules["psycopg_pool"] = fake_pool

    # Provide a minimal bcrypt substitute (not actually used because we stub to_thread)
    class FakeBcrypt(types.ModuleType):
        def hashpw(self, pw: bytes, salt: bytes) -> bytes:
            return b"hashed"

        def gensalt(self, rounds: int = 12) -> bytes:
            return b"salt"

    # Replace bcrypt with a lightweight fake for tests.
    sys.modules["bcrypt"] = FakeBcrypt("bcrypt")

    class FakeLogger:
        def info(self, *a: Any, **k: Any) -> None:
            return None

        def warning(self, *a: Any, **k: Any) -> None:
            return None

        def exception(self, *a: Any, **k: Any) -> None:
            return None

    class FakeStructlog(types.ModuleType):
        def get_logger(self) -> FakeLogger:
            return FakeLogger()

    # Replace structlog to avoid noisy logging in tests.
    sys.modules["structlog"] = FakeStructlog("structlog")

    # Import by file path to avoid package name issues (hyphens)
    import importlib.util
    from importlib.machinery import ModuleSpec, SourceFileLoader
    from pathlib import Path

    bootstrap_path = Path(__file__).parents[1] / "app" / "bootstrap.py"
    spec: ModuleSpec | None = importlib.util.spec_from_file_location(
        "auth_bootstrap", str(bootstrap_path)
    )
    if (
        spec is None
        or spec.loader is None
        or not isinstance(spec.loader, SourceFileLoader)
    ):
        raise ImportError("Could not load module spec or loader for bootstrap.py")
    bootstrap_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap_mod)
    sys.modules[spec.name] = bootstrap_mod
    return bootstrap_mod


@pytest.mark.asyncio
async def test_ensure_admin_creates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")

    # Stub asyncio.to_thread to avoid real bcrypt work
    async def to_thread_stub(
        fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> bytes:
        return b"hashed"

    monkeypatch.setattr(asyncio, "to_thread", to_thread_stub, raising=False)

    bootstrap_mod = _import_with_fakes(exists=False)

    # Run the coroutine
    await bootstrap_mod.ensure_admin()

    # Clean up sys.modules to avoid caching issues
    sys.modules.pop("auth_bootstrap", None)

    # No exceptions should be raised; function should complete successfully.


@pytest.mark.asyncio
async def test_ensure_admin_skips_when_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")

    async def to_thread_stub(
        fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> bytes:
        return b"hashed"

    monkeypatch.setattr(asyncio, "to_thread", to_thread_stub)

    bootstrap_mod = _import_with_fakes(exists=True)

    # Should not raise
    await bootstrap_mod.ensure_admin()

    # Clean up sys.modules to avoid caching issues
    sys.modules.pop("auth_bootstrap", None)
