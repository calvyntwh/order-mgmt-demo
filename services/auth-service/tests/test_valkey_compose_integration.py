import logging
import os
import time

import httpx
import pytest


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION", "0") != "1",
    reason="Integration tests disabled by default",
)
def test_login_refresh_logout_against_compose():
    """Integration test that exercises login -> refresh rotation -> logout flows
    against a locally running compose stack (auth-service + valkey + postgres).

    Requirements: run `docker compose -f docker-compose.mvp.yml up -d --build`
    and ensure services are reachable on localhost:8001 (auth-service) and
    valkey is available. Set RUN_INTEGRATION=1 when running pytest to enable.
    """
    auth_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

    # basic retry/wait for service readiness
    deadline = time.time() + 30
    logger = logging.getLogger(__name__)
    while time.time() < deadline:
        try:
            r = httpx.get(f"{auth_url}/health", timeout=2)
            if r.status_code == 200:
                break
        except Exception as exc:  # log and retry
            logger.debug("health check attempt failed: %s", exc)
        time.sleep(1)
    else:
        pytest.skip("Auth service not available on localhost:8001")

    client = httpx.Client()

    username = f"int-user-{int(time.time())}"
    pw = "password123"

    # register
    r = client.post(f"{auth_url}/register", json={"username": username, "password": pw})
    assert r.status_code in (200, 201)

    # token
    r = client.post(f"{auth_url}/token", json={"username": username, "password": pw})
    assert r.status_code == 200
    data = r.json()
    refresh = data.get("refresh_token")
    assert refresh

    # refresh (rotate)
    r2 = client.post(f"{auth_url}/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    new = r2.json().get("refresh_token")
    assert new and new != refresh

    # old should be invalid now
    r3 = client.post(f"{auth_url}/refresh", json={"refresh_token": refresh})
    assert r3.status_code == 401

    # logout (revoke)
    # obtain access token via refreshing the new token
    r4 = client.post(f"{auth_url}/refresh", json={"refresh_token": new})
    assert r4.status_code == 200
    access = r4.json().get("access_token")
    assert access

    headers = {"Authorization": f"Bearer {access}"}
    r5 = client.post(f"{auth_url}/logout", headers=headers)
    assert r5.status_code == 200

    # subsequent refresh with the last refresh token should fail
    r6 = client.post(f"{auth_url}/refresh", json={"refresh_token": new})
    assert r6.status_code == 401
