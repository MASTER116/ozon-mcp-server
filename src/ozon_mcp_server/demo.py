"""
Demo mode — realistic mock data for all Ozon API endpoints.

When DEMO_MODE=true, the server runs without real Ozon API keys,
Redis, or PostgreSQL. All tools return realistic marketplace data.

Usage:
    DEMO_MODE=true python -m ozon_mcp_server
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Demo response data — realistic Ozon marketplace products
# ---------------------------------------------------------------------------

DEMO_PRODUCTS = {
    987210451: {
        "id": 987210451,
        "name": "Наушники Apple AirPods Pro 2 (USB-C), белый",
        "offer_id": "WH-AIRPODS-PRO-2",
        "barcode": "4670126290118",
        "category_id": 15621031,
        "price": "18990.00",
        "old_price": "24990.00",
        "premium_price": "17490.00",
        "marketing_price": "18990.00",
        "currency_code": "RUB",
        "stocks": {"present": 124, "reserved": 17},
        "visibility_details": {"has_price": True, "has_stock": True, "active_product": True},
        "status": {"state": "processed", "is_created": True, "moderate_status": "approved"},
        "rating": 4.8,
        "images": ["https://cdn1.ozone.ru/s3/multimedia/1234567890.jpg"],
        "created_at": "2025-09-15T08:32:00Z",
        "updated_at": "2026-04-03T14:20:00Z",
    },
    987210452: {
        "id": 987210452,
        "name": "Пылесос Dyson V15 Detect Absolute, золотой",
        "offer_id": "WH-DYSON-V15-GOLD",
        "barcode": "5025155076224",
        "category_id": 14621033,
        "price": "54990.00",
        "old_price": "69990.00",
        "currency_code": "RUB",
        "stocks": {"present": 37, "reserved": 5},
        "visibility_details": {"has_price": True, "has_stock": True, "active_product": True},
        "status": {"state": "processed", "is_created": True, "moderate_status": "approved"},
        "rating": 4.9,
        "created_at": "2025-07-20T10:15:00Z",
        "updated_at": "2026-04-02T09:00:00Z",
    },
    987210453: {
        "id": 987210453,
        "name": "Чемодан Samsonite Lite-Shock, 75 см, чёрный",
        "offer_id": "WH-SAMSONITE-LITE",
        "barcode": "5414847854329",
        "category_id": 13721045,
        "price": "32490.00",
        "old_price": "42990.00",
        "currency_code": "RUB",
        "stocks": {"present": 18, "reserved": 2},
        "visibility_details": {"has_price": True, "has_stock": True, "active_product": True},
        "status": {"state": "processed", "is_created": True, "moderate_status": "approved"},
        "rating": 4.7,
        "created_at": "2025-11-01T12:00:00Z",
        "updated_at": "2026-03-28T16:30:00Z",
    },
    987210454: {
        "id": 987210454,
        "name": "Беспроводная колонка JBL Flip 6, чёрный",
        "offer_id": "WH-JBL-FLIP6-BLK",
        "barcode": "6925281993145",
        "category_id": 15621032,
        "price": "7990.00",
        "old_price": "9990.00",
        "currency_code": "RUB",
        "stocks": {"present": 256, "reserved": 31},
        "visibility_details": {"has_price": True, "has_stock": True, "active_product": True},
        "status": {"state": "processed", "is_created": True, "moderate_status": "approved"},
        "rating": 4.6,
        "created_at": "2025-08-10T14:45:00Z",
        "updated_at": "2026-04-04T11:10:00Z",
    },
    987210455: {
        "id": 987210455,
        "name": "Кроссовки Nike Pegasus 41, размер 43",
        "offer_id": "WH-NIKE-PEGASUS-41",
        "barcode": "1960003867019",
        "category_id": 17121055,
        "price": "12490.00",
        "old_price": "15990.00",
        "currency_code": "RUB",
        "stocks": {"present": 42, "reserved": 8},
        "visibility_details": {"has_price": True, "has_stock": True, "active_product": True},
        "status": {"state": "processed", "is_created": True, "moderate_status": "approved"},
        "rating": 4.5,
        "created_at": "2026-01-05T09:20:00Z",
        "updated_at": "2026-04-03T18:00:00Z",
    },
}

DEMO_WAREHOUSES = [
    {"warehouse_id": 22143901, "name": "Склад Москва-Север (FBS)", "status": "working"},
    {"warehouse_id": 22143902, "name": "Склад Казань (FBS)", "status": "working"},
    {"warehouse_id": 1020000136, "name": "Ozon Хоругвино (FBO)", "status": "working"},
]

DEMO_FBS_ORDERS = [
    {
        "posting_number": "89721045-0012-1",
        "order_number": "89721045-0012",
        "status": "awaiting_packaging",
        "in_process_at": "2026-04-03T16:42:00Z",
        "shipment_date": "2026-04-04T18:00:00Z",
        "products": [
            {"name": "Наушники Apple AirPods Pro 2 (USB-C), белый", "offer_id": "WH-AIRPODS-PRO-2", "quantity": 1, "price": "18990.00", "sku": 987210451}
        ],
        "analytics_data": {"region": "Москва", "city": "Москва", "delivery_type": "PVZ"},
        "financial_data": {"products": [{"commission_amount": 2848.50, "payout": 16141.50}]},
    },
    {
        "posting_number": "89721045-0013-1",
        "order_number": "89721045-0013",
        "status": "awaiting_packaging",
        "in_process_at": "2026-04-03T18:15:00Z",
        "shipment_date": "2026-04-04T18:00:00Z",
        "products": [
            {"name": "Беспроводная колонка JBL Flip 6, чёрный", "offer_id": "WH-JBL-FLIP6-BLK", "quantity": 2, "price": "7990.00", "sku": 987210454}
        ],
        "analytics_data": {"region": "Санкт-Петербург", "city": "Санкт-Петербург", "delivery_type": "Courier"},
        "financial_data": {"products": [{"commission_amount": 2397.00, "payout": 13583.00}]},
    },
    {
        "posting_number": "89721045-0014-1",
        "order_number": "89721045-0014",
        "status": "awaiting_packaging",
        "in_process_at": "2026-04-04T09:03:00Z",
        "shipment_date": "2026-04-05T18:00:00Z",
        "products": [
            {"name": "Кроссовки Nike Pegasus 41, размер 43", "offer_id": "WH-NIKE-PEGASUS-41", "quantity": 1, "price": "12490.00", "sku": 987210455}
        ],
        "analytics_data": {"region": "Новосибирск", "city": "Новосибирск", "delivery_type": "PVZ"},
        "financial_data": {"products": [{"commission_amount": 1873.50, "payout": 10616.50}]},
    },
]

DEMO_FBO_ORDERS = [
    {
        "posting_number": "FBO-78412690-0001",
        "status": "delivered",
        "in_process_at": "2026-03-30T12:00:00Z",
        "products": [
            {"name": "Пылесос Dyson V15 Detect Absolute, золотой", "offer_id": "WH-DYSON-V15-GOLD", "quantity": 1, "price": "54990.00", "sku": 987210452}
        ],
        "analytics_data": {"region": "Краснодар", "city": "Краснодар", "delivery_type": "PVZ"},
    },
]

DEMO_ANALYTICS = {
    "data": [
        {"dimensions": [{"id": "2026-03-29", "name": "29.03.2026"}], "metrics": [287450.00, 18, 3420]},
        {"dimensions": [{"id": "2026-03-30", "name": "30.03.2026"}], "metrics": [341200.00, 24, 4150]},
        {"dimensions": [{"id": "2026-03-31", "name": "31.03.2026"}], "metrics": [198700.00, 12, 2870]},
        {"dimensions": [{"id": "2026-04-01", "name": "01.04.2026"}], "metrics": [425600.00, 31, 5210]},
        {"dimensions": [{"id": "2026-04-02", "name": "02.04.2026"}], "metrics": [389100.00, 27, 4890]},
        {"dimensions": [{"id": "2026-04-03", "name": "03.04.2026"}], "metrics": [512300.00, 38, 6340]},
    ],
    "totals": [2154350.00, 150, 26880],
}

DEMO_FINANCE = {
    "operations": [
        {
            "operation_date": "2026-04-03T00:00:00Z",
            "operation_type": "OperationAgentDeliveredToCustomer",
            "posting_number": "89721045-0010-1",
            "items": [{"name": "Наушники Apple AirPods Pro 2 (USB-C), белый", "sku": 987210451}],
            "accruals_for_sale": 18990.00,
            "sale_commission": -2848.50,
            "amount": 16141.50,
        },
        {
            "operation_date": "2026-04-02T00:00:00Z",
            "operation_type": "OperationAgentDeliveredToCustomer",
            "posting_number": "FBO-78412690-0001",
            "items": [{"name": "Пылесос Dyson V15 Detect Absolute, золотой", "sku": 987210452}],
            "accruals_for_sale": 54990.00,
            "sale_commission": -8248.50,
            "amount": 46741.50,
        },
    ],
    "page_count": 1,
    "row_count": 2,
}


# ---------------------------------------------------------------------------
# DemoOzonClient — replaces real OzonClient in demo mode
# ---------------------------------------------------------------------------

class DemoOzonClient:
    """Mock Ozon API client that returns demo data."""

    async def request(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        logger.debug("demo_api_request", endpoint=endpoint)

        if endpoint == "/v2/product/list":
            items = [{"product_id": pid, "offer_id": p["offer_id"]} for pid, p in DEMO_PRODUCTS.items()]
            return {"result": {"items": items, "total": len(items), "last_id": str(items[-1]["product_id"])}}

        if endpoint == "/v2/product/info":
            pid = payload.get("product_id", 0)
            oid = payload.get("offer_id", "")
            sku = payload.get("sku", 0)
            for product in DEMO_PRODUCTS.values():
                if product["id"] == pid or product["offer_id"] == oid or product["id"] == sku:
                    return {"result": product}
            return {"result": list(DEMO_PRODUCTS.values())[0]}

        if endpoint == "/v1/product/info/stocks":
            rows = []
            for pid, p in DEMO_PRODUCTS.items():
                rows.append({
                    "product_id": pid,
                    "offer_id": p["offer_id"],
                    "stocks": [
                        {"type": "fbs", "present": p["stocks"]["present"], "reserved": p["stocks"]["reserved"], "warehouse_name": "Склад Москва-Север"},
                        {"type": "fbo", "present": p["stocks"]["present"] * 3, "reserved": p["stocks"]["reserved"] * 2, "warehouse_name": "Ozon Хоругвино"},
                    ],
                })
            return {"result": {"rows": rows}}

        if endpoint == "/v1/product/import/prices":
            results = []
            for price_item in payload.get("prices", []):
                results.append({"product_id": price_item.get("product_id", 0), "updated": True, "errors": []})
            return {"result": results}

        if endpoint == "/v2/products/stocks":
            results = []
            for stock_item in payload.get("stocks", []):
                results.append({"product_id": stock_item.get("product_id", 0), "updated": True, "errors": []})
            return {"result": results}

        if endpoint == "/v1/product/archive":
            return {"result": True}

        if endpoint == "/v3/product/import":
            return {"result": {"task_id": 348901562, "product_id": 0}}

        if endpoint == "/v3/posting/fbs/list":
            status_filter = payload.get("filter", {}).get("status", "awaiting_packaging")
            postings = [o for o in DEMO_FBS_ORDERS if o["status"] == status_filter]
            if not postings:
                postings = DEMO_FBS_ORDERS
            return {"result": {"postings": postings, "has_next": False}}

        if endpoint == "/v2/posting/fbo/list":
            return {"result": {"postings": DEMO_FBO_ORDERS, "has_next": False}}

        if endpoint == "/v1/analytics/data":
            return {"result": DEMO_ANALYTICS, "timestamp": "2026-04-04T10:00:00Z"}

        if endpoint == "/v3/finance/transaction/list":
            return {"result": DEMO_FINANCE}

        if endpoint == "/v1/warehouse/list":
            return {"result": DEMO_WAREHOUSES}

        return {"result": {}}

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# DemoCache — in-memory cache (no Redis needed)
# ---------------------------------------------------------------------------

class DemoCache:
    """In-memory cache for demo mode."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, category: str, params: Any) -> Any:
        return None  # Always miss — show fresh data

    async def set(self, category: str, params: Any, data: Any, ttl: int = 300) -> None:
        pass

    async def invalidate(self, category: str) -> int:
        return 0


# ---------------------------------------------------------------------------
# DemoRateLimiter — always allows (no Redis needed)
# ---------------------------------------------------------------------------

class DemoRateLimiter:
    """Rate limiter that always passes in demo mode."""

    async def check_global(self, rpm: int) -> None:
        pass

    async def check_write(self, rpm: int) -> None:
        pass


# ---------------------------------------------------------------------------
# DemoAuditLogger — logs to structlog (no PostgreSQL needed)
# ---------------------------------------------------------------------------

class DemoAuditLogger:
    """Audit logger that writes to console in demo mode."""

    async def init_schema(self) -> None:
        pass

    async def log(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None,
        result_status: str,
        response_time_ms: float,
        error_message: str | None = None,
        ozon_trace_id: str | None = None,
    ) -> uuid.UUID:
        record_id = uuid.uuid4()
        logger.info(
            "demo_audit",
            tool=tool_name,
            status=result_status,
            ms=round(response_time_ms, 1),
        )
        return record_id

    async def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return []

    async def cleanup(self, days: int = 90) -> int:
        return 0
