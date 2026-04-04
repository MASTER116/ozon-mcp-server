"""
Security middleware: credential leak prevention in tool responses.

Prevents API keys, tokens, and passwords from leaking through:
- Tool responses
- Error messages
- Tracebacks
"""

from __future__ import annotations

import functools
import re
from collections.abc import Callable
from typing import Any

import structlog

logger = structlog.get_logger()

# Patterns for detecting secrets in strings
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[a-f0-9]{32,64}", re.IGNORECASE), "***HEX_KEY***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer ***MASKED***"),
    (re.compile(
        r"(api[_-]?key|password|secret|token|credential|auth)"
        r"\s*[:=]\s*['\"]?[^\s'\"]{8,}",
        re.IGNORECASE,
    ), "\\1=***MASKED***"),
]

# Dictionary keys whose values are always masked
_SENSITIVE_KEYS = frozenset({
    "api_key", "apikey", "api-key",
    "password", "passwd",
    "secret", "token",
    "authorization", "auth",
    "client_secret",
    "access_token", "refresh_token",
})


def sanitize_string(value: str) -> str:
    """Mask potential secrets in a string."""
    result = value
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def sanitize_value(data: Any, _depth: int = 0) -> Any:
    """
    Recursively mask secrets in a data structure.

    Recursion depth limited to 10 levels (DoS protection).
    """
    if _depth > 10:
        return data

    if isinstance(data, str):
        return sanitize_string(data)

    if isinstance(data, dict):
        result = {}
        for key, val in data.items():
            key_lower = str(key).lower().replace("-", "_")
            if key_lower in _SENSITIVE_KEYS:
                result[key] = "***MASKED***"
            else:
                result[key] = sanitize_value(val, _depth + 1)
        return result

    if isinstance(data, list):
        return [sanitize_value(item, _depth + 1) for item in data]

    return data


def sanitize_error(exc: Exception) -> str:
    """Mask secrets in an error message."""
    msg = str(exc)
    return sanitize_string(msg)


def sanitize_output(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to sanitize tool output, preventing credential leaks."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = await func(*args, **kwargs)
        if isinstance(result, dict):
            return sanitize_value(result)
        return result

    return wrapper
