"""Tests for order and analytics MCP tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from tests.conftest import (
    ANALYTICS_RESPONSE,
    FBS_ORDERS_RESPONSE,
    FINANCE_REPORT_RESPONSE,
    WAREHOUSE_LIST_RESPONSE,
)


class TestGetFbsOrders:
    async def test_returns_api_result(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_fbs_orders

        mock_app_context.ozon.request = AsyncMock(return_value=FBS_ORDERS_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_fbs_orders(ctx=mock_ctx)

        assert result == FBS_ORDERS_RESPONSE
        mock_app_context.ozon.request.assert_awaited_once()
        endpoint = mock_app_context.ozon.request.call_args[0][0]
        assert endpoint == "/v3/posting/fbs/list"

    async def test_cached(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_fbs_orders

        mock_app_context.cache.get = AsyncMock(return_value=FBS_ORDERS_RESPONSE)

        result = await get_fbs_orders(ctx=mock_ctx)

        assert result == FBS_ORDERS_RESPONSE
        mock_app_context.ozon.request.assert_not_awaited()

    async def test_custom_params(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_fbs_orders

        mock_app_context.ozon.request = AsyncMock(return_value=FBS_ORDERS_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        await get_fbs_orders(status="delivered", days_back=30, limit=100, ctx=mock_ctx)

        payload = mock_app_context.ozon.request.call_args[0][1]
        assert payload["filter"]["status"] == "delivered"
        assert payload["limit"] == 100


class TestGetFboOrders:
    async def test_returns_api_result(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_fbo_orders

        mock_app_context.ozon.request = AsyncMock(return_value={"result": {"postings": []}})
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_fbo_orders(ctx=mock_ctx)

        endpoint = mock_app_context.ozon.request.call_args[0][0]
        assert endpoint == "/v2/posting/fbo/list"

    async def test_custom_params(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_fbo_orders

        mock_app_context.ozon.request = AsyncMock(return_value={"result": {"postings": []}})

        await get_fbo_orders(status="delivered", days_back=14, limit=200, ctx=mock_ctx)

        payload = mock_app_context.ozon.request.call_args[0][1]
        assert payload["filter"]["status"] == "delivered"
        assert payload["limit"] == 200


class TestGetAnalytics:
    async def test_returns_api_result(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_analytics

        mock_app_context.ozon.request = AsyncMock(return_value=ANALYTICS_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_analytics(
            date_from="2026-03-29", date_to="2026-04-03", ctx=mock_ctx,
        )

        assert result == ANALYTICS_RESPONSE
        endpoint = mock_app_context.ozon.request.call_args[0][0]
        assert endpoint == "/v1/analytics/data"

    async def test_missing_dates_returns_error(self, mock_ctx):
        from ozon_mcp_server.tools.order_tools import get_analytics

        result = await get_analytics(ctx=mock_ctx)

        assert "error" in result

    async def test_cached(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_analytics

        mock_app_context.cache.get = AsyncMock(return_value=ANALYTICS_RESPONSE)

        result = await get_analytics(
            date_from="2026-03-29", date_to="2026-04-03", ctx=mock_ctx,
        )

        assert result == ANALYTICS_RESPONSE
        mock_app_context.ozon.request.assert_not_awaited()

    async def test_custom_metrics(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_analytics

        mock_app_context.ozon.request = AsyncMock(return_value=ANALYTICS_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        await get_analytics(
            date_from="2026-03-29",
            date_to="2026-04-03",
            metrics=["revenue", "returns"],
            dimensions=["week"],
            ctx=mock_ctx,
        )

        payload = mock_app_context.ozon.request.call_args[0][1]
        assert payload["metrics"] == ["revenue", "returns"]
        assert payload["dimension"] == ["week"]


class TestGetFinanceReport:
    async def test_returns_api_result(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_finance_report

        mock_app_context.ozon.request = AsyncMock(return_value=FINANCE_REPORT_RESPONSE)

        result = await get_finance_report(
            date_from="2026-04-01", date_to="2026-04-03", ctx=mock_ctx,
        )

        assert result == FINANCE_REPORT_RESPONSE
        endpoint = mock_app_context.ozon.request.call_args[0][0]
        assert endpoint == "/v3/finance/transaction/list"

    async def test_missing_dates_returns_error(self, mock_ctx):
        from ozon_mcp_server.tools.order_tools import get_finance_report

        result = await get_finance_report(ctx=mock_ctx)

        assert "error" in result


class TestGetWarehouseList:
    async def test_returns_api_result(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_warehouse_list

        mock_app_context.ozon.request = AsyncMock(return_value=WAREHOUSE_LIST_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_warehouse_list(ctx=mock_ctx)

        assert result == WAREHOUSE_LIST_RESPONSE
        endpoint = mock_app_context.ozon.request.call_args[0][0]
        assert endpoint == "/v1/warehouse/list"

    async def test_cached(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.order_tools import get_warehouse_list

        mock_app_context.cache.get = AsyncMock(return_value=WAREHOUSE_LIST_RESPONSE)

        result = await get_warehouse_list(ctx=mock_ctx)

        assert result == WAREHOUSE_LIST_RESPONSE
        mock_app_context.ozon.request.assert_not_awaited()
