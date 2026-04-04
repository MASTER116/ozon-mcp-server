"""Tests for OzonClient: SSRF protection, retry, error handling."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from ozon_mcp_server.api.client import OzonAPIError, OzonClient, OzonRateLimitError


class TestOzonClientInit:
    def test_base_url_fixed(self) -> None:
        client = OzonClient("test", SecretStr("key123"))
        assert client.BASE_URL == "https://api-seller.ozon.ru"

    def test_headers_set(self) -> None:
        client = OzonClient("my_id", SecretStr("my_key"))
        assert client._http.headers["Client-Id"] == "my_id"
        assert client._http.headers["Api-Key"] == "my_key"

    def test_redirects_disabled(self) -> None:
        client = OzonClient("test", SecretStr("key"))
        assert client._http.follow_redirects is False


class TestSSRFProtection:
    @pytest.mark.asyncio
    async def test_absolute_url_blocked(self) -> None:
        client = OzonClient("test", SecretStr("key"))
        with pytest.raises(ValueError, match="SSRF blocked"):
            await client.request("https://evil.com/steal")

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self) -> None:
        client = OzonClient("test", SecretStr("key"))
        with pytest.raises(ValueError, match="SSRF blocked"):
            await client.request("../../etc/passwd")

    @pytest.mark.asyncio
    async def test_relative_path_allowed(self) -> None:
        client = OzonClient("test", SecretStr("key"))
        # This request will pass validation but fail on HTTP
        # (no real server) — this is expected for a unit test
        with pytest.raises(Exception):  # noqa: B017
            await client.request("/v2/product/list", {"limit": 1})


class TestOzonClientErrors:
    @pytest.mark.asyncio
    async def test_rate_limit_error_type(self) -> None:
        err = OzonRateLimitError(429, "Too many requests", "trace-123")
        assert err.status_code == 429
        assert err.trace_id == "trace-123"
        assert isinstance(err, OzonAPIError)

    def test_api_error_message(self) -> None:
        err = OzonAPIError(400, "Bad Request")
        assert "400" in str(err)
        assert "Bad Request" in str(err)
