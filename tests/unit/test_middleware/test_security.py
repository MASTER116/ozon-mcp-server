"""Tests for security middleware: secret masking."""

from __future__ import annotations

from ozon_mcp_server.middleware.security import sanitize_string, sanitize_value


class TestSanitizeString:
    def test_hex_key_masked(self) -> None:
        result = sanitize_string("key=abcdef1234567890abcdef1234567890")
        assert "abcdef1234567890" not in result
        assert "MASKED" in result or "HEX_KEY" in result

    def test_bearer_token_masked(self) -> None:
        result = sanitize_string("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.test")
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert "MASKED" in result

    def test_safe_string_unchanged(self) -> None:
        result = sanitize_string("This is a normal product name")
        assert result == "This is a normal product name"

    def test_password_in_text_masked(self) -> None:
        result = sanitize_string("api_key=super_secret_value_12345678")
        assert "super_secret" not in result


class TestSanitizeValue:
    def test_dict_sensitive_keys(self) -> None:
        data = {
            "name": "Test",
            "api_key": "real_secret_key_123",
            "token": "bearer_token_456",
            "price": "1999.00",
        }
        result = sanitize_value(data)
        assert result["name"] == "Test"
        assert result["api_key"] == "***MASKED***"
        assert result["token"] == "***MASKED***"
        assert result["price"] == "1999.00"

    def test_nested_dict(self) -> None:
        data = {
            "config": {
                "password": "my_password",
                "host": "localhost",
            }
        }
        result = sanitize_value(data)
        assert result["config"]["password"] == "***MASKED***"
        assert result["config"]["host"] == "localhost"

    def test_list_sanitization(self) -> None:
        data = ["normal", {"secret": "hidden"}]
        result = sanitize_value(data)
        assert result[0] == "normal"
        assert result[1]["secret"] == "***MASKED***"

    def test_depth_limit(self) -> None:
        """Deep nesting does not cause recursion deeper than 10 levels."""
        data: dict = {"level": {}}
        current = data["level"]
        for _ in range(20):
            current["next"] = {}
            current = current["next"]
        current["secret"] = "should_not_crash"
        # Should not crash
        result = sanitize_value(data)
        assert result is not None

    def test_none_passthrough(self) -> None:
        assert sanitize_value(None) is None

    def test_int_passthrough(self) -> None:
        assert sanitize_value(42) == 42
