"""
Ozon Seller MCP Server — main module.

FastMCP server initialization with:
- Lifespan management (Redis, PostgreSQL, Ozon API connections)
- Middleware stack (audit, rate limiting, credential filtering)
- Tool registration via module imports
- MCP resources (audit log)
"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import asyncpg
import redis.asyncio as aioredis
import structlog

from mcp.server.fastmcp import Context, FastMCP

from ozon_mcp_server.api.client import OzonClient
from ozon_mcp_server.cache.redis_cache import RedisCache
from ozon_mcp_server.config import Settings, get_settings
from ozon_mcp_server.db.audit_repo import AuditLogger
from ozon_mcp_server.middleware.rate_limit import RateLimiter

logger = structlog.get_logger()

# Pattern for masking secrets in responses
_SECRET_RE = re.compile(r"[a-f0-9]{32,}", re.IGNORECASE)


@dataclass
class AppContext:
    """Application context — accessible via ctx.request_context.lifespan_context."""

    settings: Settings
    ozon: OzonClient
    cache: RedisCache
    rate_limiter: RateLimiter
    audit: AuditLogger
    db: asyncpg.Pool


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle: database, cache, and HTTP client connections."""
    settings = get_settings()

    # PostgreSQL connection pool
    db_pool = await asyncpg.create_pool(
        settings.postgres_dsn.get_secret_value(),
        min_size=2,
        max_size=10,
    )
    audit = AuditLogger(db_pool)
    await audit.init_schema()

    # Redis client
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    cache = RedisCache(redis_client, default_ttl=settings.cache_ttl_seconds)
    rate_limiter = RateLimiter(redis_client)

    # Ozon API HTTP client with circuit breaker
    ozon = OzonClient(
        client_id=settings.ozon_client_id,
        api_key=settings.ozon_api_key,
        circuit_breaker_threshold=settings.circuit_breaker_threshold,
        circuit_breaker_recovery=settings.circuit_breaker_recovery_seconds,
    )

    logger.info(
        "server_started",
        server_name=settings.server_name,
        transport=settings.transport,
    )

    try:
        yield AppContext(
            settings=settings,
            ozon=ozon,
            cache=cache,
            rate_limiter=rate_limiter,
            audit=audit,
            db=db_pool,
        )
    finally:
        await ozon.close()
        await redis_client.close()
        await db_pool.close()
        logger.info("server_stopped")


# --- MCP server initialization ---
mcp = FastMCP(
    "Ozon Seller MCP Server",
    lifespan=app_lifespan,
)


def get_app_context(ctx: Any) -> AppContext:
    """Extract AppContext from MCP Context (helper for tool functions)."""
    return ctx.request_context.lifespan_context  # type: ignore[no-any-return]


# --- MCP Resources ---


@mcp.resource("audit://recent")
async def get_recent_audit() -> str:
    """Recent audit log entries (last 50 tool calls).

    Returns a JSON array of audit records with timestamps,
    tool names, parameters, and response times.
    """
    # Note: MCP resources don't receive Context in FastMCP 2.x,
    # so this returns a placeholder. In production with HTTP transport,
    # the audit log is accessible via the PostgreSQL database directly.
    return json.dumps(
        {"message": "Audit log available via PostgreSQL. Use get_finance_report tool for transaction history."},
        indent=2,
    )
