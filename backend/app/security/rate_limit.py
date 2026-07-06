"""
In-memory token-bucket rate limiter.

IMPORTANT: This implementation is keyed per-process. When running with
multiple Uvicorn workers (--workers N) each worker has an independent
bucket, effectively multiplying limits by N. For multi-worker or
multi-instance deployments replace this with a Redis-backed limiter
(e.g. slowapi + redis or a custom implementation using redis-py).

The Docker image is configured to run a single worker to keep this
correct out of the box. Scale horizontally with multiple containers
instead of multiple workers per container.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from app.core.config import settings
from app.core.exceptions import RateLimitError


class RateLimiter:
    """Sliding-window rate limiter keyed by ``(identity, scope)``."""

    def __init__(self, per_minute: int | None = None) -> None:
        self.per_minute = per_minute or settings.rate_limit_per_min
        self._buckets: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, identity: str, scope: str = "default") -> None:
        """Raise :class:`RateLimitError` if the identity exceeded its budget."""
        async with self._lock:
            now = time.monotonic()
            window = 60.0
            bucket = self._buckets[(identity, scope)]
            # Drop entries outside the window
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= self.per_minute:
                retry_after = int(window - (now - bucket[0])) + 1
                raise RateLimitError(
                    detail="Too many requests",
                    code="rate_limited",
                    extras={"retry_after": retry_after},
                )
            bucket.append(now)


limiter = RateLimiter()
