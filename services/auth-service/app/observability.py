import logging
import sys
import uuid
from collections.abc import Callable

import structlog
from fastapi import Request


def setup_logging() -> None:
    # Configure a minimal structlog JSON renderer for structured logs in the demo.
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
    # Ensure stdlib logs are visible and routed to stdout so tests can capture
    # the emitted structured JSON. Use force=True to replace existing handlers.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, force=True)


async def request_id_middleware(request: Request, call_next: Callable):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # bind into both request state and structlog contextvars so logs include it
    request.state.request_id = rid
    structlog.contextvars.bind_contextvars(request_id=rid)
    try:
        response = await call_next(request)
    except Exception as exc:  # capture and return a 500 response with request id
        logger = structlog.get_logger()
        logger.exception("unhandled exception in request", exc_info=exc)
        from starlette.responses import PlainTextResponse

        resp = PlainTextResponse("Internal Server Error", status_code=500)
        resp.headers["X-Request-ID"] = rid
        structlog.contextvars.clear_contextvars()
        return resp
    else:
        # ensure header is present on the normal response
        response.headers["X-Request-ID"] = rid
        structlog.contextvars.clear_contextvars()
        return response


def inject_request_id_headers(headers: dict | None, request: Request | None) -> dict:
    """Return headers with X-Request-ID injected when available from request.state or structlog contextvars."""
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
