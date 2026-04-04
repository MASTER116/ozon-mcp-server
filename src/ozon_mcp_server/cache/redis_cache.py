"""
Redis caching for Ozon API responses.

Strategy:
- GET requests are cached with configurable TTL
- Write operations invalidate related cache entries
- Key format: ozon:{category}:{parameter_hash}
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()


class RedisCache:
    """Redis cache manager with TTL and category-based invalidation."""

    PREFIX = "ozon"

    def __init__(self, client: aioredis.Redis, default_ttl: int = 300) -> None:
        self._redis = client
        self._default_ttl = default_ttl

    @staticmethod
    def _hash_params(params: dict[str, Any]) -> str:
        """SHA256 hash of parameters for unique cache keys."""
        raw = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _key(self, category: str, params: dict[str, Any]) -> str:
        """Generate cache key: ozon:{category}:{hash}."""
        return f"{self.PREFIX}:{category}:{self._hash_params(params)}"

    async def get(self, category: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """Get a value from cache."""
        key = self._key(category, params)
        raw = await self._redis.get(key)
        if raw is None:
            return None
        logger.debug("cache_hit", key=key)
        result: dict[str, Any] = json.loads(raw)
        return result

    async def set(
        self,
        category: str,
        params: dict[str, Any],
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Store a value in cache with TTL."""
        key = self._key(category, params)
        raw = json.dumps(value, default=str)
        await self._redis.setex(key, ttl or self._default_ttl, raw)
        logger.debug("cache_set", key=key, ttl=ttl or self._default_ttl)

    async def invalidate(self, category: str) -> int:
        """Invalidate all keys in a category (after write operations)."""
        pattern = f"{self.PREFIX}:{category}:*"
        keys: list[str] = []
        async for key in self._redis.scan_iter(match=pattern, count=100):
            keys.append(key)
        if keys:
            deleted = await self._redis.delete(*keys)
            logger.info("cache_invalidated", category=category, count=deleted)
            return int(deleted)
        return 0

    async def invalidate_all(self) -> int:
        """Full cache flush (for tests or emergency situations)."""
        pattern = f"{self.PREFIX}:*"
        keys: list[str] = []
        async for key in self._redis.scan_iter(match=pattern, count=100):
            keys.append(key)
        if keys:
            deleted = await self._redis.delete(*keys)
            logger.info("cache_full_invalidation", count=deleted)
            return int(deleted)
        return 0
