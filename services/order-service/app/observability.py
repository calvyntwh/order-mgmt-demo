import logging
import uuid
from collections.abc import Callable

import structlog
from fastapi import Request


def setup_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logging.basicConfig(level=logging.INFO)


async def request_id_middleware(request: Request, call_next: Callable):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = rid
    structlog.contextvars.bind_contextvars(request_id=rid)
    try:
        response = await call_next(request)
    except Exception as exc:
        logger = structlog.get_logger()
        logger.exception("unhandled exception in request", exc_info=exc)
        from starlette.responses import PlainTextResponse

        resp = PlainTextResponse("Internal Server Error", status_code=500)
        resp.headers["X-Request-ID"] = rid
        structlog.contextvars.clear_contextvars()
        return resp
    else:
        response.headers["X-Request-ID"] = rid
        structlog.contextvars.clear_contextvars()
        return response


def inject_request_id_headers(headers: dict | None, request: Request | None) -> dict:
    out = dict(headers or {})
    rid = None
    if request is not None:
        rid = getattr(request.state, "request_id", None)
    if not rid:
        try:
            rid = structlog.contextvars.get_contextvars().get("request_id")
        except Exception:
            rid = None
    if rid:
        out["X-Request-ID"] = rid
    return out
