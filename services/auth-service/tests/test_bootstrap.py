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


def _import_with_fakes(exists: bool = False):
    # Insert fake asyncpg module into sys.modules before importing
    fake = FakeAsyncPGModule(exists=exists)
    sys.modules.setdefault("asyncpg", fake)

    # Provide a minimal bcrypt substitute (not actually used because we stub to_thread)
    class FakeBcrypt(types.ModuleType):
        def hashpw(self, pw: bytes, salt: bytes) -> bytes:
            return b"hashed"

        def gensalt(self, rounds: int = 12) -> bytes:
            return b"salt"

    sys.modules.setdefault("bcrypt", FakeBcrypt("bcrypt"))

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

    sys.modules.setdefault("structlog", FakeStructlog("structlog"))

    # Import by file path to avoid package name issues (hyphens)
    import importlib.util
    from importlib.machinery import ModuleSpec, SourceFileLoader
    from pathlib import Path

    bootstrap_path = Path(__file__).parents[1] / "app" / "bootstrap.py"
    spec: ModuleSpec | None = importlib.util.spec_from_file_location(
        "auth_bootstrap", str(bootstrap_path)
    )
    if spec is None or not isinstance(spec.loader, SourceFileLoader):
        raise ImportError("Could not load module spec or loader for bootstrap.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_ensure_admin_creates(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")

    # Stub asyncio.to_thread to avoid real bcrypt work
    async def to_thread_stub(
        fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> bytes:
        return b"hashed"

    monkeypatch.setattr(asyncio, "to_thread", to_thread_stub)

    mod = _import_with_fakes(exists=False)

    # Run the coroutine
    asyncio.run(mod.ensure_admin())

    # No exceptions should be raised; function should complete successfully.


def test_ensure_admin_skips_when_exists(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")

    async def to_thread_stub(
        fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> bytes:
        return b"hashed"

    monkeypatch.setattr(asyncio, "to_thread", to_thread_stub)

    mod = _import_with_fakes(exists=True)

    # Should not raise
    asyncio.run(mod.ensure_admin())
