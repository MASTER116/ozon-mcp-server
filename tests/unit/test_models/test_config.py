"""Tests for configuration and settings validation."""

from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from ozon_mcp_server.config import Settings


class TestSettings:
    def test_default_values(self) -> None:
        s = Settings(
            ozon_client_id="test",
            ozon_api_key=SecretStr("test_key"),
        )
        assert s.ozon_api_base_url == "https://api-seller.ozon.ru"
        assert s.redis_url == "redis://localhost:6379/0"
        assert s.rate_limit_rpm == 100
        assert s.log_level == "INFO"

    def test_base_url_override_blocked(self) -> None:
        with pytest.raises(ValidationError, match="SSRF"):
            Settings(
                ozon_client_id="test",
                ozon_api_key=SecretStr("test_key"),
                ozon_api_base_url="https://evil.com",
            )

    def test_log_level_validation(self) -> None:
        s = Settings(
            ozon_client_id="test",
            ozon_api_key=SecretStr("key"),
            log_level="debug",
        )
        assert s.log_level == "DEBUG"

    def test_invalid_log_level(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                ozon_client_id="test",
                ozon_api_key=SecretStr("key"),
                log_level="TRACE",
            )

    def test_rate_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                ozon_client_id="test",
                ozon_api_key=SecretStr("key"),
                rate_limit_rpm=0,
            )

    def test_port_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                ozon_client_id="test",
                ozon_api_key=SecretStr("key"),
                port=80,
            )

    def test_secret_str_not_leaked(self) -> None:
        s = Settings(
            ozon_client_id="test",
            ozon_api_key=SecretStr("super_secret_123"),
        )
        # SecretStr masks the value
        assert "super_secret_123" not in str(s)
        assert "super_secret_123" not in repr(s)
        # But get_secret_value() returns the original
        assert s.ozon_api_key.get_secret_value() == "super_secret_123"
