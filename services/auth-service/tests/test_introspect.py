from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import create_token
from app.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/auth")
client = TestClient(app)


def test_introspect():
    token = create_token(sub="u1", username="tester", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/auth/introspect", headers=headers)
    if r.status_code != 200:
        raise AssertionError(f"Expected status 200, got {r.status_code}")
    body = r.json()
    if body["username"] != "tester":
        raise AssertionError(f"Expected username 'tester', got {body['username']}")
    if body["is_admin"] is not True:
        raise AssertionError(f"Expected is_admin True, got {body['is_admin']}")
