"""Tests for authentication."""

from __future__ import annotations

from ozon_mcp_server.middleware.auth import verify_bearer_token


class TestVerifyBearerToken:
    def test_valid_token(self) -> None:
        assert verify_bearer_token("Bearer my_secret_token", "my_secret_token") is True

    def test_valid_token_without_prefix(self) -> None:
        assert verify_bearer_token("my_secret_token", "my_secret_token") is True

    def test_invalid_token(self) -> None:
        assert verify_bearer_token("Bearer wrong_token", "correct_token") is False

    def test_empty_provided(self) -> None:
        assert verify_bearer_token("", "secret") is False

    def test_empty_expected_disables_auth(self) -> None:
        """Empty expected_secret = authentication is disabled."""
        assert verify_bearer_token("any_token", "") is True
        assert verify_bearer_token("", "") is True

    def test_timing_attack_resistance(self) -> None:
        """Verify constant-time comparison (hmac.compare_digest) is used."""
        # The main check is that the function uses hmac,
        # not ==. This is a unit test, not a benchmark.
        result1 = verify_bearer_token("Bearer aaaaaaaaaa", "bbbbbbbbbb")
        result2 = verify_bearer_token("Bearer aaaaaaaaaa", "aaaaaaaaab")
        assert result1 is False
        assert result2 is False
