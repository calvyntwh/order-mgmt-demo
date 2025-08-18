import bcrypt
import pytest


@pytest.mark.parametrize("password", ["abc12345", "securepassword", "anotherpass"])
def test_hash_and_verify(password: str) -> None:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    if not bcrypt.checkpw(password.encode("utf-8"), hashed):
        raise AssertionError("Password verification failed for correct password.")
    if bcrypt.checkpw(b"wrongpassword", hashed):
        raise AssertionError("Password verification succeeded for wrong password.")
