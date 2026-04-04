"""
MCP client authentication.

For stdio transport, authentication is implicit (local process).
For HTTP transport: Bearer token in the Authorization header.
"""

from __future__ import annotations

import hmac

import structlog

logger = structlog.get_logger()


class AuthError(Exception):
    """Authentication error."""


def verify_bearer_token(provided: str, expected_secret: str) -> bool:
    """
    Verify a Bearer token using constant-time comparison.

    Constant-time comparison prevents timing attacks.
    """
    if not expected_secret:
        # Authentication disabled (empty token in settings)
        return True

    if not provided:
        return False

    # Strip "Bearer " prefix
    token = provided.removeprefix("Bearer ").strip()

    return hmac.compare_digest(token.encode(), expected_secret.encode())
