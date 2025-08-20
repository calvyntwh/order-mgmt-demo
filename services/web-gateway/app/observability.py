import logging
import sys
import uuid
from typing import Callable

import structlog
import json
from fastapi import Request


def setup_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    # Processor to print JSON to stdout so pytest's capfd can capture it. This
    # is intentionally simple for the demo tests and avoids relying solely on
    # the stdlib logging capture which pytest may separate from stdout.
    def _print_json(_, __, event_dict):
        try:
            sys.stdout.write(json.dumps(event_dict) + "\n")
        except Exception:
            pass
        return event_dict
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _print_json,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    # Ensure stdlib logs are visible and routed to stdout so tests capturing
    # stdout/stderr (capfd) can observe structlog output.
    # Use force=True to replace any existing handlers during test runs.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, force=True)


async def request_id_middleware(request: Request, call_next: Callable):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # attach to state and bind to structlog contextvars
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
    """Helper to inject X-Request-ID into outbound headers when request state is present.

    Callers can use this to ensure inter-service calls include the request id for tracing.
    """
    out = dict(headers or {})
    rid = None
    if request is not None:
        rid = getattr(request.state, "request_id", None)
    if not rid:
        # fallback to structlog contextvars
        try:
            rid = structlog.contextvars.get_contextvars().get("request_id")
        except Exception:
            rid = None
    if rid:
        out["X-Request-ID"] = rid
    return out
