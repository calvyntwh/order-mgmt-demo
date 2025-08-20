from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import router as auth_router


def test_refresh_rotates_token():
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    client = TestClient(app)

    # create a token by calling /token (uses dummy DB in tests)
    # the tests in this repo's auth service use a dummy DB; here we'll bypass DB and
    # directly simulate by calling the token endpoint with proper test user created
    # via bootstrap; but simpler: call create_token not exposed here. For now, call /token
    # with invalid credentials and expect 401 unless the DB is prepared. Instead, emulate
    # rotation by creating a refresh token directly using the store helper.
    # For this test, we'll import the store functions.
    from app.auth import store_refresh_token, is_refresh_revoked, rotate_refresh_token

    # simulate storing refresh token for user 'u1'
    old = "rt-old-test"
    store_refresh_token(old, sub="u1")
    assert not is_refresh_revoked(old)

    new = rotate_refresh_token(old)
    assert new is not None
    assert is_refresh_revoked(old)
    assert not is_refresh_revoked(new)
