import logging
import uuid
from typing import Callable

from fastapi import Request


def setup_logging() -> None:
    # Minimal structured logging configuration for the demo.
    fmt = '{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
    logging.basicConfig(level=logging.INFO, format=fmt)


async def request_id_middleware(request: Request, call_next: Callable):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # attach to state for handlers to read
    request.state.request_id = rid
    # ensure it's present on the response
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response
