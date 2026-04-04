"""
Redis-backed rate limiter (Token Bucket).

Three levels of limits:
- Global: max requests to Ozon API per minute
- Per-tool: destructive operations (update_prices, etc.) — lower limit
- Per-session: protection against AI agent retry storms
"""

from __future__ import annotations

import time

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()


class RateLimitExceeded(Exception):
    """Rate limit exceeded."""

    def __init__(self, limit: int, window: int, key: str):
        self.limit = limit
        self.window = window
        self.key = key
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window}s (key: {key})"
        )


class RateLimiter:
    """Token Bucket rate limiter backed by Redis."""

    PREFIX = "ratelimit"

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> bool:
        """
        Check and register a request against the rate limit.

        Args:
            key: Unique key (e.g., "global", "tool:update_prices")
            max_requests: Max requests allowed in the window
            window_seconds: Window size in seconds

        Returns:
            True if the request is allowed

        Raises:
            RateLimitExceeded: When the limit is exceeded
        """
        full_key = f"{self.PREFIX}:{key}"
        now = time.time()
        window_start = now - window_seconds

        pipe = self._redis.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(full_key, 0, window_start)
        # Count current entries
        pipe.zcard(full_key)
        # Add new entry
        pipe.zadd(full_key, {str(now): now})
        # Set TTL (slightly longer than window)
        pipe.expire(full_key, window_seconds + 10)

        results = await pipe.execute()
        current_count: int = results[1]

        if current_count >= max_requests:
            logger.warning(
                "rate_limit_exceeded",
                key=key,
                current=current_count,
                limit=max_requests,
            )
            raise RateLimitExceeded(max_requests, window_seconds, key)

        return True

    async def check_global(self, max_rpm: int) -> bool:
        """Check the global rate limit."""
        return await self.check("global", max_rpm, 60)

    async def check_write(self, max_rpm: int) -> bool:
        """Check the write operations rate limit."""
        return await self.check("write", max_rpm, 60)

    async def get_remaining(self, key: str, max_requests: int) -> int:
        """Get the remaining number of allowed requests."""
        full_key = f"{self.PREFIX}:{key}"
        now = time.time()
        await self._redis.zremrangebyscore(full_key, 0, now - 60)
        current = await self._redis.zcard(full_key)
        return max(0, max_requests - int(current))
