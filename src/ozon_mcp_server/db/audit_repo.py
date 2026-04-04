"""
Audit logging of MCP tool invocations to PostgreSQL.

Every tool call is recorded: tool name, parameters, result, response time.
Secrets are masked before storage.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg
import structlog

logger = structlog.get_logger()

# Patterns for masking secrets in parameters/responses
_SECRET_PATTERNS = [
    re.compile(r"[a-f0-9]{32,}", re.IGNORECASE),  # API keys
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),  # Bearer tokens
    re.compile(r"(password|secret|token|api[_-]?key)\s*[:=]\s*\S+", re.IGNORECASE),
]

# SQL for creating the audit table
CREATE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tool_name TEXT NOT NULL,
    parameters JSONB,
    result_status TEXT NOT NULL CHECK (result_status IN (
        'success', 'error', 'rate_limited', 'unauthorized', 'validation_error'
    )),
    response_time_ms DOUBLE PRECISION,
    error_message TEXT,
    ozon_trace_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_tool ON audit_log (tool_name);
"""


def mask_secrets(data: Any) -> Any:
    """Mask potential secrets in data before logging."""
    if isinstance(data, str):
        result = data
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub("***MASKED***", result)
        return result
    if isinstance(data, dict):
        return {k: mask_secrets(v) for k, v in data.items()}
    if isinstance(data, list):
        return [mask_secrets(item) for item in data]
    return data


class AuditLogger:
    """Audit logger with PostgreSQL storage."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def init_schema(self) -> None:
        """Create the audit table (idempotent)."""
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_AUDIT_TABLE)
        logger.info("audit_schema_initialized")

    async def log(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None,
        result_status: str,
        response_time_ms: float,
        error_message: str | None = None,
        ozon_trace_id: str | None = None,
    ) -> uuid.UUID:
        """Record an audit event."""
        record_id = uuid.uuid4()
        safe_params = mask_secrets(parameters) if parameters else None

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_log
                        (id, tool_name, parameters, result_status,
                         response_time_ms, error_message, ozon_trace_id)
                    VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7)
                    """,
                    record_id,
                    tool_name,
                    __import__("json").dumps(safe_params, default=str) if safe_params else None,
                    result_status,
                    response_time_ms,
                    error_message,
                    ozon_trace_id,
                )
        except Exception:
            # Audit must never crash the main flow
            logger.exception("audit_log_failed", tool=tool_name)

        return record_id

    async def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent audit entries (for the audit://recent MCP resource)."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, timestamp, tool_name, parameters, result_status,
                       response_time_ms, error_message, ozon_trace_id
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT $1
                """,
                min(limit, 500),
            )
        return [dict(row) for row in rows]

    async def cleanup(self, days: int = 90) -> int:
        """Delete audit entries older than N days."""
        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM audit_log WHERE timestamp < $1 - INTERVAL '1 day' * $2",
                cutoff, days,
            )
        count = int(result.split()[-1])
        logger.info("audit_cleanup", deleted=count, older_than_days=days)
        return count
