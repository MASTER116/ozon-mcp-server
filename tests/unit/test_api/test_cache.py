"""Tests for RedisCache."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ozon_mcp_server.cache.redis_cache import RedisCache


async def _empty_async_iter(**kwargs: Any) -> AsyncIterator[str]:
    """Async iterator that yields nothing (mock for scan_iter)."""
    return
    yield  # noqa: F401 — makes this an async generator


@pytest.fixture()
def cache() -> RedisCache:
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock(return_value=1)
    redis.scan_iter = MagicMock(side_effect=lambda **kw: _empty_async_iter(**kw))
    return RedisCache(redis, default_ttl=300)


class TestRedisCache:
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache: RedisCache) -> None:
        result = await cache.get("products", {"limit": 100})
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit(self) -> None:
        data = {"result": [1, 2, 3]}
        redis = MagicMock()
        redis.get = AsyncMock(return_value=json.dumps(data))
        c = RedisCache(redis, default_ttl=300)

        result = await c.get("products", {"limit": 100})
        assert result == data

    @pytest.mark.asyncio
    async def test_cache_set(self, cache: RedisCache) -> None:
        await cache.set("products", {"limit": 100}, {"result": []}, ttl=600)
        cache._redis.setex.assert_called_once()  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_cache_invalidate_empty(self, cache: RedisCache) -> None:
        count = await cache.invalidate("products")
        assert count == 0

    def test_key_generation_deterministic(self, cache: RedisCache) -> None:
        key1 = cache._key("products", {"a": 1, "b": 2})
        key2 = cache._key("products", {"b": 2, "a": 1})
        assert key1 == key2  # sort_keys=True

    def test_key_generation_different_params(self, cache: RedisCache) -> None:
        key1 = cache._key("products", {"limit": 10})
        key2 = cache._key("products", {"limit": 20})
        assert key1 != key2

    def test_key_prefix(self, cache: RedisCache) -> None:
        key = cache._key("products", {})
        assert key.startswith("ozon:products:")
