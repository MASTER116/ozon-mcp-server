"""
Entry point: python -m ozon_mcp_server

Supports transports: stdio (default), streamable-http, sse.
"""

from __future__ import annotations

import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if __import__("sys").stderr.isatty()
        else structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

# Import server and all tool modules to trigger @mcp.tool registration
from ozon_mcp_server.config import get_settings
from ozon_mcp_server.server import mcp

import ozon_mcp_server.tools.product_tools  # noqa: F401
import ozon_mcp_server.tools.order_tools  # noqa: F401

logger = structlog.get_logger()


def main() -> None:
    """Start the MCP server."""
    settings = get_settings()

    logger.info(
        "starting_mcp_server",
        name=settings.server_name,
        transport=settings.transport,
        port=settings.port if settings.transport != "stdio" else None,
    )

    mcp.run(transport=settings.transport)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
