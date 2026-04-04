"""Tests for product MCP tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from tests.conftest import (
    CREATE_PRODUCT_RESPONSE,
    PRODUCT_INFO_RESPONSE,
    PRODUCT_LIST_RESPONSE,
    STOCK_ON_WAREHOUSES_RESPONSE,
    UPDATE_PRICES_RESPONSE,
    UPDATE_STOCKS_RESPONSE,
)


class TestGetProductList:
    async def test_returns_api_result(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_list

        mock_app_context.ozon.request = AsyncMock(return_value=PRODUCT_LIST_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_product_list(ctx=mock_ctx)

        assert result == PRODUCT_LIST_RESPONSE
        mock_app_context.ozon.request.assert_awaited_once()
        mock_app_context.audit.log.assert_awaited()

    async def test_returns_cached_result(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_list

        mock_app_context.cache.get = AsyncMock(return_value=PRODUCT_LIST_RESPONSE)

        result = await get_product_list(ctx=mock_ctx)

        assert result == PRODUCT_LIST_RESPONSE
        mock_app_context.ozon.request.assert_not_awaited()

    async def test_visibility_filter(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_list

        mock_app_context.ozon.request = AsyncMock(return_value=PRODUCT_LIST_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        await get_product_list(visibility="ARCHIVED", ctx=mock_ctx)

        call_payload = mock_app_context.ozon.request.call_args[0][1]
        assert call_payload["filter"]["visibility"] == "ARCHIVED"

    async def test_with_last_id(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_list

        mock_app_context.ozon.request = AsyncMock(return_value=PRODUCT_LIST_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        await get_product_list(last_id="987210455", ctx=mock_ctx)

        call_payload = mock_app_context.ozon.request.call_args[0][1]
        assert call_payload["last_id"] == "987210455"


class TestGetProductInfo:
    async def test_by_product_id(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_info

        mock_app_context.ozon.request = AsyncMock(return_value=PRODUCT_INFO_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_product_info(product_id=987210451, ctx=mock_ctx)

        assert result == PRODUCT_INFO_RESPONSE

    async def test_by_offer_id(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_info

        mock_app_context.ozon.request = AsyncMock(return_value=PRODUCT_INFO_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_product_info(offer_id="WH-AIRPODS-PRO-2", ctx=mock_ctx)

        assert result == PRODUCT_INFO_RESPONSE

    async def test_by_sku(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_info

        mock_app_context.ozon.request = AsyncMock(return_value=PRODUCT_INFO_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_product_info(sku=987210451, ctx=mock_ctx)

        assert result == PRODUCT_INFO_RESPONSE

    async def test_no_identifier_returns_error(self, mock_ctx):
        from ozon_mcp_server.tools.product_tools import get_product_info

        result = await get_product_info(ctx=mock_ctx)

        assert "error" in result

    async def test_cached(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_product_info

        mock_app_context.cache.get = AsyncMock(return_value=PRODUCT_INFO_RESPONSE)

        result = await get_product_info(product_id=987210451, ctx=mock_ctx)

        assert result == PRODUCT_INFO_RESPONSE
        mock_app_context.ozon.request.assert_not_awaited()


class TestGetStockOnWarehouses:
    async def test_by_product_ids(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_stock_on_warehouses

        mock_app_context.ozon.request = AsyncMock(return_value=STOCK_ON_WAREHOUSES_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_stock_on_warehouses(product_ids=[987210451], ctx=mock_ctx)

        assert result == STOCK_ON_WAREHOUSES_RESPONSE

    async def test_by_offer_ids(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_stock_on_warehouses

        mock_app_context.ozon.request = AsyncMock(return_value=STOCK_ON_WAREHOUSES_RESPONSE)
        mock_app_context.cache.get = AsyncMock(return_value=None)

        result = await get_stock_on_warehouses(offer_ids=["WH-AIRPODS-PRO-2"], ctx=mock_ctx)

        assert result == STOCK_ON_WAREHOUSES_RESPONSE

    async def test_no_filter_returns_error(self, mock_ctx):
        from ozon_mcp_server.tools.product_tools import get_stock_on_warehouses

        result = await get_stock_on_warehouses(ctx=mock_ctx)

        assert "error" in result

    async def test_cached(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import get_stock_on_warehouses

        mock_app_context.cache.get = AsyncMock(return_value=STOCK_ON_WAREHOUSES_RESPONSE)

        result = await get_stock_on_warehouses(product_ids=[987210451], ctx=mock_ctx)

        assert result == STOCK_ON_WAREHOUSES_RESPONSE
        mock_app_context.ozon.request.assert_not_awaited()


class TestUpdatePrices:
    async def test_success(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import update_prices

        mock_app_context.ozon.request = AsyncMock(return_value=UPDATE_PRICES_RESPONSE)

        prices = [{"product_id": 987210451, "price": "17990.00"}]
        result = await update_prices(prices=prices, ctx=mock_ctx)

        assert result == UPDATE_PRICES_RESPONSE
        mock_app_context.ozon.request.assert_awaited_once()


class TestUpdateStocks:
    async def test_success(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import update_stocks

        mock_app_context.ozon.request = AsyncMock(return_value=UPDATE_STOCKS_RESPONSE)

        stocks = [{"product_id": 987210451, "stock": 200, "warehouse_id": 22143901}]
        result = await update_stocks(stocks=stocks, ctx=mock_ctx)

        assert result == UPDATE_STOCKS_RESPONSE
        mock_app_context.ozon.request.assert_awaited_once()


class TestArchiveProduct:
    async def test_success(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import archive_product

        mock_app_context.ozon.request = AsyncMock(return_value={"result": True})

        result = await archive_product(product_ids=[987210451], ctx=mock_ctx)

        assert result == {"result": True}
        call_payload = mock_app_context.ozon.request.call_args[0][1]
        assert call_payload["product_id"] == [987210451]


class TestCreateProduct:
    async def test_success(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import create_product

        mock_app_context.ozon.request = AsyncMock(return_value=CREATE_PRODUCT_RESPONSE)

        result = await create_product(
            name="Наушники Sony WH-1000XM5",
            offer_id="WH-SONY-XM5",
            category_id=15621031,
            price="29990.00",
            weight=250,
            width=200,
            height=250,
            depth=50,
            description="Беспроводные наушники с шумоподавлением",
            ctx=mock_ctx,
        )

        assert result == CREATE_PRODUCT_RESPONSE
        mock_app_context.ozon.request.assert_awaited_once()

    async def test_with_images(self, mock_ctx, mock_app_context):
        from ozon_mcp_server.tools.product_tools import create_product

        mock_app_context.ozon.request = AsyncMock(return_value=CREATE_PRODUCT_RESPONSE)

        await create_product(
            name="Test",
            offer_id="TEST-001",
            category_id=100,
            price="999.00",
            weight=100,
            width=100,
            height=100,
            depth=100,
            images=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            ctx=mock_ctx,
        )

        call_payload = mock_app_context.ozon.request.call_args[0][1]
        images = call_payload["items"][0]["images"]
        assert len(images) == 2
        assert images[0]["default"] is True
        assert images[1]["default"] is False
