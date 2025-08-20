import asyncio
import os

import pytest

from scripts import e2e_smoke


@pytest.mark.asyncio
async def test_e2e_smoke_runs():
    """Run the repository's e2e smoke against services expected at localhost ports.

    CI will start services via docker-compose; this test simply re-uses the existing
    `scripts/e2e_smoke.py::run_smoke` helper to exercise register→token→create order.
    """
    # Allow overriding service URLs for CI via env vars (workflow sets them)
    os.environ.setdefault("AUTH_SERVICE_URL", os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"))
    os.environ.setdefault("ORDER_SERVICE_URL", os.getenv("ORDER_SERVICE_URL", "http://localhost:8002"))

    # run the smoke script's coroutine; errors will fail the test
    await e2e_smoke.run_smoke()
