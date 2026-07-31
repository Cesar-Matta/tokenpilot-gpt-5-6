"""API-key authentication and bounded in-memory rate limiting."""

from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import Settings


class SlidingWindowRateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, identifier: str) -> None:
        now = time.monotonic()
        events = self._events[identifier]
        while events and events[0] <= now - 60:
            events.popleft()
        if len(events) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again in one minute.",
                headers={"Retry-After": "60"},
            )
        events.append(now)


def authenticate(request: Request, api_key: str | None, settings: Settings) -> str:
    """Validate a client key in constant time when protection is enabled."""
    if not settings.require_api_key:
        return request.client.host if request.client else "anonymous"
    if not settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API-key protection is enabled but TOKENPILOT_API_KEYS is not configured.",
        )
    if not api_key or not any(
        secrets.compare_digest(api_key, known) for known in settings.api_keys
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")
    return f"key:{api_key[:8]}"
