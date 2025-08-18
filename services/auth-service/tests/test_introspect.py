from fastapi import FastAPI
from httpx import AsyncClient

from app.auth import router as auth_router, _create_token

app = FastAPI()
app.include_router(auth_router)


async def test_introspect():
    token = _create_token(sub="u1", username="tester", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/auth/introspect", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["username"] == "tester"
        assert body["is_admin"] is True
