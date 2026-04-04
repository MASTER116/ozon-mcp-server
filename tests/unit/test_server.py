"""Tests for server.py — AppContext, get_app_context, MCP instance, resource."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from ozon_mcp_server.server import AppContext, get_app_context, get_recent_audit, mcp


class TestGetAppContext:
    def test_extracts_context(self, mock_ctx, mock_app_context):
        result = get_app_context(mock_ctx)
        assert result is mock_app_context

    def test_returns_app_context_type(self, mock_ctx, mock_app_context):
        result = get_app_context(mock_ctx)
        assert isinstance(result, AppContext)


class TestAppContext:
    def test_dataclass_fields(self, mock_app_context):
        assert hasattr(mock_app_context, "settings")
        assert hasattr(mock_app_context, "ozon")
        assert hasattr(mock_app_context, "cache")
        assert hasattr(mock_app_context, "rate_limiter")
        assert hasattr(mock_app_context, "audit")
        assert hasattr(mock_app_context, "db")


class TestMcpInstance:
    def test_mcp_name(self):
        assert mcp.name == "Ozon Seller MCP Server"


class TestGetRecentAudit:
    async def test_returns_json_string(self):
        result = await get_recent_audit()
        parsed = json.loads(result)
        assert "message" in parsed
