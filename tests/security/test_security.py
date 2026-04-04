"""
Security tests: SSRF, injection, credential leak.

These tests verify that the MCP server is resistant to the main attack vectors
from OWASP MCP Top 10.
"""

from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from ozon_mcp_server.api.client import OzonClient
from ozon_mcp_server.config import Settings
from ozon_mcp_server.middleware.security import sanitize_value
from ozon_mcp_server.models.products import GetProductListParams, UpdatePricesParams


class TestSSRFPrevention:
    """MCP01/MCP06: SSRF via URL manipulation."""

    @pytest.mark.asyncio
    async def test_absolute_url_blocked(self) -> None:
        client = OzonClient("test", SecretStr("key"))
        with pytest.raises(ValueError, match="SSRF"):
            await client.request("https://evil.com/exfiltrate")

    @pytest.mark.asyncio
    async def test_http_url_blocked(self) -> None:
        client = OzonClient("test", SecretStr("key"))
        with pytest.raises(ValueError, match="SSRF"):
            await client.request("http://169.254.169.254/metadata")

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self) -> None:
        client = OzonClient("test", SecretStr("key"))
        with pytest.raises(ValueError, match="SSRF"):
            await client.request("../../../etc/passwd")

    def test_base_url_override_blocked(self) -> None:
        with pytest.raises(Exception):
            Settings(
                ozon_client_id="test",
                ozon_api_key=SecretStr("key"),
                ozon_api_base_url="https://evil.com",
            )


class TestPromptInjection:
    """MCP03/MCP06: Prompt injection via tool parameters."""

    def test_sql_injection_in_offer_id(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(offer_ids=["'; DROP TABLE products; --"])

    def test_html_injection_in_offer_id(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(offer_ids=["<script>alert('xss')</script>"])

    def test_unicode_trickery(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(offer_ids=["test\x00hidden"])

    def test_price_injection(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePricesParams(prices=[
                {"product_id": 1, "price": "100 OR 1=1"},
            ])

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePricesParams(prices=[
                {"product_id": 1, "price": "-999.99"},
            ])


class TestCredentialLeakPrevention:
    """MCP01/MCP10: Secret leakage via responses and logs."""

    def test_api_key_in_dict_masked(self) -> None:
        data = {"api_key": "real_secret_abcdef1234567890", "name": "Product"}
        result = sanitize_value(data)
        assert result["api_key"] == "***MASKED***"
        assert result["name"] == "Product"

    def test_token_in_nested_dict_masked(self) -> None:
        data = {"config": {"token": "bearer_xyz_secret"}}
        result = sanitize_value(data)
        assert result["config"]["token"] == "***MASKED***"

    def test_hex_key_in_string_masked(self) -> None:
        from ozon_mcp_server.middleware.security import sanitize_string
        result = sanitize_string("Error: key=abcdef1234567890abcdef1234567890")
        assert "abcdef1234567890abcdef1234567890" not in result

    def test_secret_str_repr_masked(self) -> None:
        """Pydantic SecretStr masks the value in repr."""
        secret = SecretStr("my_api_key_12345")
        assert "my_api_key_12345" not in repr(secret)
        assert "**" in repr(secret)

    def test_settings_repr_masks_secrets(self) -> None:
        s = Settings(
            ozon_client_id="test",
            ozon_api_key=SecretStr("super_secret_key_123"),
        )
        repr_str = repr(s)
        assert "super_secret_key_123" not in repr_str


class TestInputBoundaries:
    """Boundary value tests — protection against DoS and overflow."""

    def test_max_limit_product_list(self) -> None:
        p = GetProductListParams(limit=1000)
        assert p.limit == 1000

    def test_overflow_limit_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(limit=999_999)

    def test_max_offer_ids(self) -> None:
        ids = [f"SKU-{i:04d}" for i in range(1000)]
        p = GetProductListParams(offer_ids=ids)
        assert len(p.offer_ids) == 1000

    def test_overflow_offer_ids_rejected(self) -> None:
        ids = [f"SKU-{i:04d}" for i in range(1001)]
        with pytest.raises(ValidationError):
            GetProductListParams(offer_ids=ids)

    def test_max_prices_batch(self) -> None:
        prices = [{"product_id": i, "price": "100.00"} for i in range(1, 1001)]
        p = UpdatePricesParams(prices=prices)
        assert len(p.prices) == 1000

    def test_overflow_prices_rejected(self) -> None:
        prices = [{"product_id": i, "price": "100.00"} for i in range(1, 1002)]
        with pytest.raises(ValidationError):
            UpdatePricesParams(prices=prices)
