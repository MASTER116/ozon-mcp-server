"""
HTTP client for Ozon Seller API.

Security features:
- Fixed base_url (SSRF protection)
- Redirect following disabled
- SecretStr for API key (never logged)
- Retry with exponential backoff for 429/5xx
- Request timeouts
- Circuit breaker for cascading failure prevention
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from typing import Any

import httpx
import structlog
from pydantic import SecretStr
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()

# Private IP ranges — blocked for SSRF protection
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("fc00::/7"),
]


class OzonAPIError(Exception):
    """Ozon API error."""

    def __init__(self, status_code: int, message: str, trace_id: str | None = None):
        self.status_code = status_code
        self.message = message
        self.trace_id = trace_id
        super().__init__(f"Ozon API {status_code}: {message}")


class OzonRateLimitError(OzonAPIError):
    """Ozon API rate limit exceeded (429)."""


class CircuitBreakerOpenError(OzonAPIError):
    """Circuit breaker is open — Ozon API is temporarily unavailable."""

    def __init__(self) -> None:
        super().__init__(
            503,
            "Circuit breaker open: Ozon API temporarily unavailable, retry later",
        )


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures when Ozon API is down.

    States:
    - CLOSED: normal operation, requests pass through
    - OPEN: all requests rejected immediately (after threshold failures)
    - HALF_OPEN: one probe request allowed (after recovery timeout)
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self._failure_count: int = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float = 0.0
        self._state: str = "closed"
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        return self._state

    async def check(self) -> None:
        """Check if request is allowed. Raises CircuitBreakerOpenError if not."""
        async with self._lock:
            if self._state == "closed":
                return
            if self._state == "open":
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self._recovery_timeout:
                    self._state = "half_open"
                    logger.info("circuit_breaker_half_open")
                    return
                raise CircuitBreakerOpenError()
            # half_open — allow one probe request
            return

    async def record_success(self) -> None:
        """Record a successful request."""
        async with self._lock:
            if self._state == "half_open":
                logger.info("circuit_breaker_closed")
            self._failure_count = 0
            self._state = "closed"

    async def record_failure(self) -> None:
        """Record a failed request (5xx or timeout)."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == "half_open":
                self._state = "open"
                logger.warning("circuit_breaker_reopened")
            elif self._failure_count >= self._failure_threshold:
                self._state = "open"
                logger.warning(
                    "circuit_breaker_opened",
                    failures=self._failure_count,
                    threshold=self._failure_threshold,
                )


def _is_private_ip(host: str) -> bool:
    """Check if a host resolves to a private IP address."""
    try:
        resolved = socket.getaddrinfo(host, None)
        for _, _, _, _, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            if any(ip in network for network in _PRIVATE_NETWORKS):
                return True
    except (socket.gaierror, ValueError):
        return True  # Block on resolution failure
    return False


class OzonClient:
    """Secure HTTP client for Ozon Seller API."""

    # Fixed base URL — SSRF protection
    BASE_URL = "https://api-seller.ozon.ru"

    def __init__(
        self,
        client_id: str,
        api_key: SecretStr,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_recovery: float = 60.0,
    ) -> None:
        self._client_id = client_id
        self._api_key = api_key
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_recovery,
        )

        # SSRF check at initialization
        host = httpx.URL(self.BASE_URL).host
        if host and _is_private_ip(host):
            msg = f"SSRF blocked: {host} resolves to private IP"
            raise ValueError(msg)

        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Client-Id": self._client_id,
                "Api-Key": self._api_key.get_secret_value(),
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=False,  # SSRF protection via redirect blocking
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, OzonRateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def request(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute a POST request to the Ozon Seller API.

        Args:
            endpoint: API path (e.g., /v2/product/list)
            payload: JSON request body

        Returns:
            Parsed JSON response

        Raises:
            CircuitBreakerOpenError: When circuit breaker is open
            OzonRateLimitError: On 429 responses
            OzonAPIError: On any other API error
        """
        # Validate endpoint — only relative paths allowed
        if endpoint.startswith(("http://", "https://")):
            msg = f"SSRF blocked: absolute URLs are forbidden ({endpoint})"
            raise ValueError(msg)
        if ".." in endpoint:
            msg = f"SSRF blocked: path traversal is forbidden ({endpoint})"
            raise ValueError(msg)

        # Circuit breaker check
        await self._circuit_breaker.check()

        log = logger.bind(endpoint=endpoint)
        log.debug("ozon_api_request", payload_keys=list((payload or {}).keys()))

        try:
            response = await self._http.post(endpoint, json=payload or {})
        except httpx.TimeoutException:
            log.warning("ozon_api_timeout")
            await self._circuit_breaker.record_failure()
            raise
        except httpx.HTTPError as exc:
            log.error("ozon_api_http_error", error=str(exc))
            await self._circuit_breaker.record_failure()
            raise OzonAPIError(0, str(exc)) from exc

        trace_id = response.headers.get("x-o3-trace-id")

        if response.status_code == 429:
            log.warning("ozon_api_rate_limit", trace_id=trace_id)
            # 429 is expected — do NOT trip circuit breaker
            raise OzonRateLimitError(429, "Rate limit exceeded", trace_id)

        if response.status_code >= 500:
            body = response.text[:500]
            log.error("ozon_api_server_error", status=response.status_code, trace_id=trace_id)
            await self._circuit_breaker.record_failure()
            raise OzonAPIError(response.status_code, body, trace_id)

        if response.status_code >= 400:
            body = response.text[:500]
            log.error("ozon_api_error", status=response.status_code, body=body, trace_id=trace_id)
            # 4xx is a client error — do NOT trip circuit breaker
            raise OzonAPIError(response.status_code, body, trace_id)

        # Success — record for circuit breaker
        await self._circuit_breaker.record_success()

        data: dict[str, Any] = response.json()
        log.debug("ozon_api_response", status=response.status_code, trace_id=trace_id)
        return data
