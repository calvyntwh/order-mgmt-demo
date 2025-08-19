import bcrypt
import pytest


@pytest.mark.parametrize("password", ["abc12345", "securepassword", "anotherpass"])
def test_hash_and_verify(password: str) -> None:
    # Use a very low cost for tests to make hashing fast while still exercising
    # the bcrypt API. Production should keep a higher rounds value.
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=4))
    if not bcrypt.checkpw(password.encode("utf-8"), hashed):
        raise AssertionError("Password verification failed for correct password.")
    if bcrypt.checkpw(b"wrongpassword", hashed):
        raise AssertionError("Password verification succeeded for wrong password.")
