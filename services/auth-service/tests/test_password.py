import bcrypt
import pytest


@pytest.mark.parametrize("password", ["abc12345", "securepassword", "anotherpass"])
def test_hash_and_verify(password):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    assert bcrypt.checkpw(password.encode("utf-8"), hashed)
    assert not bcrypt.checkpw("wrongpassword".encode("utf-8"), hashed)
