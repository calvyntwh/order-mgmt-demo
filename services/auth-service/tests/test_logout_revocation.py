from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import create_token
from app.auth import router as auth_router


def test_logout_revokes_token():
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    client = TestClient(app)

    token = create_token(sub="u1", username="tester", is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    # introspect should succeed initially
    r = client.get("/auth/introspect", headers=headers)
    assert r.status_code == 200

    # logout should revoke the token
    r2 = client.post("/auth/logout", headers=headers)
    assert r2.status_code == 200

    # introspect should now fail
    r3 = client.get("/auth/introspect", headers=headers)
    assert r3.status_code == 401
