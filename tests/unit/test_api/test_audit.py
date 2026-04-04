"""Tests for audit logger."""

from __future__ import annotations

from ozon_mcp_server.db.audit_repo import mask_secrets


class TestMaskSecrets:
    def test_hex_key_masked(self) -> None:
        data = {"key": "abcdef1234567890abcdef1234567890"}
        result = mask_secrets(data)
        assert "abcdef1234567890" not in str(result)

    def test_bearer_masked(self) -> None:
        data = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9"
        result = mask_secrets(data)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result

    def test_nested_dict(self) -> None:
        data = {"config": {"api_key": "abcdef1234567890abcdef1234567890"}}
        result = mask_secrets(data)
        assert "abcdef1234567890" not in str(result)

    def test_list(self) -> None:
        data = ["safe", "abcdef1234567890abcdef1234567890"]
        result = mask_secrets(data)
        assert "abcdef1234567890abcdef1234567890" not in str(result)

    def test_safe_data_unchanged(self) -> None:
        data = {"name": "Test Product", "price": 1999}
        result = mask_secrets(data)
        assert result == data

    def test_none_passthrough(self) -> None:
        assert mask_secrets(None) is None

    def test_int_passthrough(self) -> None:
        assert mask_secrets(42) == 42
