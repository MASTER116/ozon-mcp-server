"""Tests for rate limiter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ozon_mcp_server.middleware.rate_limit import RateLimitExceeded, RateLimiter


@pytest.fixture()
def limiter_under_limit() -> RateLimiter:
    """Rate limiter with mock Redis, count < limit."""
    redis = MagicMock()
    pipe = MagicMock()
    pipe.zremrangebyscore = MagicMock()
    pipe.zcard = MagicMock()
    pipe.zadd = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[None, 5, True, True])  # count=5
    redis.pipeline.return_value = pipe
    return RateLimiter(redis)


@pytest.fixture()
def limiter_over_limit() -> RateLimiter:
    """Rate limiter with mock Redis, count >= limit."""
    redis = MagicMock()
    pipe = MagicMock()
    pipe.zremrangebyscore = MagicMock()
    pipe.zcard = MagicMock()
    pipe.zadd = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[None, 100, True, True])  # count=100
    redis.pipeline.return_value = pipe
    return RateLimiter(redis)


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_under_limit_passes(self, limiter_under_limit: RateLimiter) -> None:
        result = await limiter_under_limit.check("test_key", max_requests=10)
        assert result is True

    @pytest.mark.asyncio
    async def test_over_limit_raises(self, limiter_over_limit: RateLimiter) -> None:
        with pytest.raises(RateLimitExceeded) as exc_info:
            await limiter_over_limit.check("test_key", max_requests=10)
        assert exc_info.value.limit == 10
        assert exc_info.value.key == "test_key"

    @pytest.mark.asyncio
    async def test_check_global(self, limiter_under_limit: RateLimiter) -> None:
        result = await limiter_under_limit.check_global(100)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_write(self, limiter_under_limit: RateLimiter) -> None:
        result = await limiter_under_limit.check_write(10)
        assert result is True


class TestRateLimitExceeded:
    def test_error_message(self) -> None:
        err = RateLimitExceeded(limit=10, window=60, key="global")
        assert "10" in str(err)
        assert "60" in str(err)
        assert "global" in str(err)
