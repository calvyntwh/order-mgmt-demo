import hashlib
from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def fast_bcrypt(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Replace bcrypt.gensalt/hashpw/checkpw with fast deterministic stubs for tests.

    This keeps tests fast while still exercising the bcrypt API contract
    (hashpw returns bytes; checkpw returns True for the original password).
    """

    try:
        import bcrypt as _bcrypt
    except ImportError:
        # If bcrypt isn't importable for some reason, nothing to patch.
        yield
        return

    def gensalt_stub(rounds: int = 12) -> bytes:
        # Return a short stable salt; not a real bcrypt salt but fine for tests.
        return b"testsalt"

    def hashpw_stub(password: bytes, salt: bytes) -> bytes:
        # Deterministic, fast hash: prefix + sha256(password)
        return b"fast$" + hashlib.sha256(password).digest()

    def checkpw_stub(password: bytes, hashed: bytes) -> bool:
        return hashed == hashpw_stub(password, b"testsalt")

    monkeypatch.setattr(_bcrypt, "gensalt", gensalt_stub, raising=False)
    monkeypatch.setattr(_bcrypt, "hashpw", hashpw_stub, raising=False)
    monkeypatch.setattr(_bcrypt, "checkpw", checkpw_stub, raising=False)

    yield
