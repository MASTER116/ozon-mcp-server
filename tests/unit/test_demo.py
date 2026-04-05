"""Tests for demo mode — DemoOzonClient, DemoCache, DemoRateLimiter, DemoAuditLogger."""

from __future__ import annotations

from ozon_mcp_server.demo import DemoAuditLogger, DemoCache, DemoOzonClient, DemoRateLimiter


class TestDemoOzonClient:
    async def test_product_list(self):
        client = DemoOzonClient()
        result = await client.request("/v2/product/list")
        assert result["result"]["total"] == 5
        assert len(result["result"]["items"]) == 5

    async def test_product_info_by_id(self):
        client = DemoOzonClient()
        result = await client.request("/v2/product/info", {"product_id": 987210451})
        assert result["result"]["name"] == "Наушники Apple AirPods Pro 2 (USB-C), белый"

    async def test_product_info_by_offer_id(self):
        client = DemoOzonClient()
        result = await client.request("/v2/product/info", {"offer_id": "WH-DYSON-V15-GOLD"})
        assert result["result"]["id"] == 987210452

    async def test_stock_on_warehouses(self):
        client = DemoOzonClient()
        result = await client.request("/v1/product/info/stocks")
        assert len(result["result"]["rows"]) == 5

    async def test_update_prices(self):
        client = DemoOzonClient()
        result = await client.request("/v1/product/import/prices", {"prices": [{"product_id": 987210451, "price": "17990.00"}]})
        assert result["result"][0]["updated"] is True

    async def test_update_stocks(self):
        client = DemoOzonClient()
        result = await client.request("/v2/products/stocks", {"stocks": [{"product_id": 987210451, "stock": 100}]})
        assert result["result"][0]["updated"] is True

    async def test_archive_product(self):
        client = DemoOzonClient()
        result = await client.request("/v1/product/archive", {"product_id": [987210451]})
        assert result["result"] is True

    async def test_create_product(self):
        client = DemoOzonClient()
        result = await client.request("/v3/product/import", {"items": [{}]})
        assert result["result"]["task_id"] == 348901562

    async def test_fbs_orders(self):
        client = DemoOzonClient()
        result = await client.request("/v3/posting/fbs/list", {"filter": {"status": "awaiting_packaging"}})
        assert len(result["result"]["postings"]) == 3

    async def test_fbo_orders(self):
        client = DemoOzonClient()
        result = await client.request("/v2/posting/fbo/list")
        assert len(result["result"]["postings"]) == 1

    async def test_analytics(self):
        client = DemoOzonClient()
        result = await client.request("/v1/analytics/data")
        assert result["result"]["totals"][0] == 2154350.00

    async def test_finance(self):
        client = DemoOzonClient()
        result = await client.request("/v3/finance/transaction/list")
        assert result["result"]["row_count"] == 2

    async def test_warehouse_list(self):
        client = DemoOzonClient()
        result = await client.request("/v1/warehouse/list")
        assert len(result["result"]) == 3

    async def test_unknown_endpoint(self):
        client = DemoOzonClient()
        result = await client.request("/v99/unknown")
        assert result == {"result": {}}

    async def test_close(self):
        client = DemoOzonClient()
        await client.close()


class TestDemoCache:
    async def test_always_misses(self):
        cache = DemoCache()
        assert await cache.get("test", {}) is None

    async def test_set_noop(self):
        cache = DemoCache()
        await cache.set("test", {}, {"data": 1})

    async def test_invalidate_noop(self):
        cache = DemoCache()
        assert await cache.invalidate("test") == 0


class TestDemoRateLimiter:
    async def test_global_passes(self):
        limiter = DemoRateLimiter()
        await limiter.check_global(100)

    async def test_write_passes(self):
        limiter = DemoRateLimiter()
        await limiter.check_write(10)


class TestDemoAuditLogger:
    async def test_log(self):
        audit = DemoAuditLogger()
        record_id = await audit.log("test_tool", {"key": "val"}, "success", 5.0)
        assert record_id is not None

    async def test_init_schema(self):
        audit = DemoAuditLogger()
        await audit.init_schema()

    async def test_get_recent(self):
        audit = DemoAuditLogger()
        assert await audit.get_recent() == []

    async def test_cleanup(self):
        audit = DemoAuditLogger()
        assert await audit.cleanup() == 0
