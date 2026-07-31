"""Small, dependency-light observability primitives."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUESTS = Counter(
    "tokenpilot_requests_total",
    "TokenPilot requests by endpoint and HTTP status.",
    ["endpoint", "status"],
)
ROUTES = Counter(
    "tokenpilot_routes_total",
    "TokenPilot route decisions by selected model tier.",
    ["tier", "domain"],
)
ESTIMATED_COST = Counter(
    "tokenpilot_estimated_cost_usd_total",
    "Sum of route-level cost estimates in USD.",
    ["tier"],
)
ACTUAL_COST = Counter(
    "tokenpilot_actual_cost_usd_total",
    "Sum of actual provider usage estimates in USD.",
    ["tier"],
)
LATENCY = Histogram(
    "tokenpilot_request_duration_seconds",
    "TokenPilot request latency.",
    ["endpoint"],
)


class JsonFormatter(logging.Formatter):
    """Emit safe request metadata without prompts, responses, or credentials."""

    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                event[key] = value
        return json.dumps(event, separators=(",", ":"))


def configure_logging(level: str) -> logging.Logger:
    logger = logging.getLogger("tokenpilot")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
