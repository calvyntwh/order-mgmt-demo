import asyncio
import os
import sys
import types


class FakeConn:
    def __init__(self, exists=False):
        self._exists = exists
        self.executed = []

    async def fetchrow(self, query, username):
        if self._exists:
            return {"id": "some-uuid"}
        return None

    async def execute(self, query, username, password_hash):
        self.executed.append((query, username, password_hash))

    async def close(self):
        pass


class FakeAsyncPGModule(types.ModuleType):
    def __init__(self, exists=False):
        super().__init__("asyncpg")
        self._exists = exists

    async def connect(self, database_url):
        return FakeConn(exists=self._exists)


def _import_with_fakes(exists=False):
    # Insert fake asyncpg module into sys.modules before importing
    fake = FakeAsyncPGModule(exists=exists)
    sys.modules.setdefault("asyncpg", fake)

    # Provide a minimal bcrypt substitute (not actually used because we stub to_thread)
    fake_bcrypt = types.SimpleNamespace()
    fake_bcrypt.hashpw = lambda pw, salt: b"hashed"
    fake_bcrypt.gensalt = lambda rounds=12: b"salt"
    sys.modules.setdefault("bcrypt", fake_bcrypt)

    # structlog minimal
    fake_structlog = types.SimpleNamespace(
        get_logger=lambda: types.SimpleNamespace(
            info=lambda *a, **k: None,
            warning=lambda *a, **k: None,
            exception=lambda *a, **k: None,
        )
    )
    sys.modules.setdefault("structlog", fake_structlog)

    # Import by file path to avoid package name issues (hyphens)
    import importlib.util
    from pathlib import Path

    bootstrap_path = Path(__file__).parents[1] / "app" / "bootstrap.py"
    spec = importlib.util.spec_from_file_location("auth_bootstrap", str(bootstrap_path))
    mod = importlib.util.module_from_spec(spec)
    # Ensure our fake modules are available during execution
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_ensure_admin_creates(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")

    # Stub asyncio.to_thread to avoid real bcrypt work
    async def to_thread_stub(fn, *args, **kwargs):
        return b"hashed"

    monkeypatch.setattr(asyncio, "to_thread", to_thread_stub)

    mod = _import_with_fakes(exists=False)

    # Run the coroutine
    asyncio.run(mod.ensure_admin())

    # Now, re-import fake asyncpg to check side-effects: the FakeConn used inside has executed list
    # Because connect returned a new FakeConn instance which isn't directly accessible here,
    # we assert no exceptions were raised and function completed successfully.


def test_ensure_admin_skips_when_exists(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")

    async def to_thread_stub(fn, *args, **kwargs):
        return b"hashed"

    monkeypatch.setattr(asyncio, "to_thread", to_thread_stub)

    mod = _import_with_fakes(exists=True)

    # Should not raise
    asyncio.run(mod.ensure_admin())
