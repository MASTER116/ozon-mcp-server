"""
Test fixtures.

- Mock Ozon API via pytest-httpx
- Test settings (no real API keys)
- Mock fixtures for Redis and PostgreSQL
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

from ozon_mcp_server.api.client import OzonClient
from ozon_mcp_server.cache.redis_cache import RedisCache
from ozon_mcp_server.config import Settings
from ozon_mcp_server.db.audit_repo import AuditLogger
from ozon_mcp_server.middleware.rate_limit import RateLimiter


async def _empty_async_iter(**kwargs: Any) -> AsyncIterator[str]:
    """Async iterator that yields nothing (mock for scan_iter)."""
    return
    yield  # noqa: F401 — makes this an async generator


@pytest.fixture()
def test_settings() -> Settings:
    """Test settings — no real API keys."""
    return Settings(
        ozon_client_id="test_client_123",
        ozon_api_key=SecretStr("test_api_key_00000000000000000000"),
        redis_url="redis://localhost:6379/15",  # Separate DB for tests
        postgres_dsn=SecretStr("postgresql://test:test@localhost:5432/test_ozon_mcp"),
        rate_limit_rpm=1000,
        rate_limit_write_rpm=100,
        log_level="DEBUG",
    )


@pytest.fixture()
def mock_ozon_client() -> AsyncMock:
    """Mock OzonClient — no real HTTP requests."""
    client = AsyncMock(spec=OzonClient)
    client.request = AsyncMock(return_value={"result": []})
    client.close = AsyncMock()
    return client


@pytest.fixture()
def mock_redis() -> MagicMock:
    """Mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock(return_value=0)
    redis.scan_iter = MagicMock(side_effect=lambda **kw: _empty_async_iter(**kw))
    redis.pipeline = MagicMock()

    # Pipeline mock
    pipe = MagicMock()
    pipe.zremrangebyscore = MagicMock()
    pipe.zcard = MagicMock()
    pipe.zadd = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[None, 0, True, True])
    redis.pipeline.return_value = pipe

    return redis


@pytest.fixture()
def mock_cache(mock_redis: MagicMock) -> RedisCache:
    """Cache with mock Redis."""
    return RedisCache(mock_redis, default_ttl=300)


@pytest.fixture()
def mock_rate_limiter(mock_redis: MagicMock) -> RateLimiter:
    """Rate limiter with mock Redis."""
    return RateLimiter(mock_redis)


@pytest.fixture()
def mock_audit() -> AsyncMock:
    """Mock audit logger."""
    audit = AsyncMock(spec=AuditLogger)
    audit.log = AsyncMock()
    audit.init_schema = AsyncMock()
    return audit


# --- Mock Ozon API responses (realistic demo data) ---

PRODUCT_LIST_RESPONSE = {
    "result": {
        "items": [
            {"product_id": 987210451, "offer_id": "WH-AIRPODS-PRO-2"},
            {"product_id": 987210452, "offer_id": "WH-DYSON-V15-GOLD"},
            {"product_id": 987210453, "offer_id": "WH-SAMSONITE-LITE"},
            {"product_id": 987210454, "offer_id": "WH-JBL-FLIP6-BLK"},
            {"product_id": 987210455, "offer_id": "WH-NIKE-PEGASUS-41"},
        ],
        "total": 147,
        "last_id": "987210455",
    }
}

PRODUCT_INFO_RESPONSE = {
    "result": {
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
        "color_image": "https://cdn1.ozone.ru/s3/multimedia/1234567891.jpg",
        "created_at": "2025-09-15T08:32:00Z",
        "updated_at": "2026-04-03T14:20:00Z",
    }
}

STOCK_ON_WAREHOUSES_RESPONSE = {
    "result": {
        "rows": [
            {
                "product_id": 987210451,
                "offer_id": "WH-AIRPODS-PRO-2",
                "stocks": [
                    {"type": "fbs", "present": 124, "reserved": 17, "warehouse_name": "Склад Москва-Север"},
                    {"type": "fbo", "present": 340, "reserved": 42, "warehouse_name": "Ozon Хоругвино"},
                ],
            },
            {
                "product_id": 987210452,
                "offer_id": "WH-DYSON-V15-GOLD",
                "stocks": [
                    {"type": "fbs", "present": 37, "reserved": 5, "warehouse_name": "Склад Москва-Север"},
                    {"type": "fbo", "present": 89, "reserved": 12, "warehouse_name": "Ozon Хоругвино"},
                ],
            },
        ]
    }
}

FBS_ORDERS_RESPONSE = {
    "result": {
        "postings": [
            {
                "posting_number": "89721045-0012-1",
                "order_number": "89721045-0012",
                "status": "awaiting_packaging",
                "in_process_at": "2026-04-03T16:42:00Z",
                "shipment_date": "2026-04-04T18:00:00Z",
                "products": [
                    {
                        "name": "Наушники Apple AirPods Pro 2 (USB-C), белый",
                        "offer_id": "WH-AIRPODS-PRO-2",
                        "quantity": 1,
                        "price": "18990.00",
                        "sku": 987210451,
                    }
                ],
                "analytics_data": {"region": "Москва", "city": "Москва", "delivery_type": "PVZ"},
                "financial_data": {
                    "products": [{"commission_amount": 2848.50, "payout": 16141.50}],
                },
            },
            {
                "posting_number": "89721045-0013-1",
                "order_number": "89721045-0013",
                "status": "awaiting_packaging",
                "in_process_at": "2026-04-03T18:15:00Z",
                "shipment_date": "2026-04-04T18:00:00Z",
                "products": [
                    {
                        "name": "Беспроводная колонка JBL Flip 6, чёрный",
                        "offer_id": "WH-JBL-FLIP6-BLK",
                        "quantity": 2,
                        "price": "7990.00",
                        "sku": 987210454,
                    }
                ],
                "analytics_data": {"region": "Санкт-Петербург", "city": "Санкт-Петербург", "delivery_type": "Courier"},
                "financial_data": {
                    "products": [{"commission_amount": 2397.00, "payout": 13583.00}],
                },
            },
            {
                "posting_number": "89721045-0014-1",
                "order_number": "89721045-0014",
                "status": "awaiting_packaging",
                "in_process_at": "2026-04-04T09:03:00Z",
                "shipment_date": "2026-04-05T18:00:00Z",
                "products": [
                    {
                        "name": "Кроссовки Nike Pegasus 41, размер 43",
                        "offer_id": "WH-NIKE-PEGASUS-41",
                        "quantity": 1,
                        "price": "12490.00",
                        "sku": 987210455,
                    }
                ],
                "analytics_data": {"region": "Новосибирск", "city": "Новосибирск", "delivery_type": "PVZ"},
                "financial_data": {
                    "products": [{"commission_amount": 1873.50, "payout": 10616.50}],
                },
            },
        ],
        "has_next": True,
    }
}

FBO_ORDERS_RESPONSE = {
    "result": {
        "postings": [
            {
                "posting_number": "FBO-78412690-0001",
                "status": "delivered",
                "in_process_at": "2026-03-30T12:00:00Z",
                "products": [
                    {
                        "name": "Пылесос Dyson V15 Detect Absolute, золотой",
                        "offer_id": "WH-DYSON-V15-GOLD",
                        "quantity": 1,
                        "price": "54990.00",
                        "sku": 987210452,
                    }
                ],
                "analytics_data": {"region": "Краснодар", "city": "Краснодар", "delivery_type": "PVZ"},
            },
        ],
        "has_next": False,
    }
}

WAREHOUSE_LIST_RESPONSE = {
    "result": [
        {"warehouse_id": 22143901, "name": "Склад Москва-Север (FBS)", "status": "working"},
        {"warehouse_id": 22143902, "name": "Склад Казань (FBS)", "status": "working"},
        {"warehouse_id": 1020000136, "name": "Ozon Хоругвино (FBO)", "status": "working"},
    ]
}

UPDATE_PRICES_RESPONSE = {
    "result": [
        {"product_id": 987210451, "offer_id": "WH-AIRPODS-PRO-2", "updated": True, "errors": []},
        {"product_id": 987210454, "offer_id": "WH-JBL-FLIP6-BLK", "updated": True, "errors": []},
    ]
}

UPDATE_STOCKS_RESPONSE = {
    "result": [
        {"product_id": 987210451, "offer_id": "WH-AIRPODS-PRO-2", "updated": True, "errors": []},
    ]
}

ANALYTICS_RESPONSE = {
    "result": {
        "data": [
            {
                "dimensions": [{"id": "2026-03-29", "name": "29.03.2026"}],
                "metrics": [287450.00, 18, 3420],
            },
            {
                "dimensions": [{"id": "2026-03-30", "name": "30.03.2026"}],
                "metrics": [341200.00, 24, 4150],
            },
            {
                "dimensions": [{"id": "2026-03-31", "name": "31.03.2026"}],
                "metrics": [198700.00, 12, 2870],
            },
            {
                "dimensions": [{"id": "2026-04-01", "name": "01.04.2026"}],
                "metrics": [425600.00, 31, 5210],
            },
            {
                "dimensions": [{"id": "2026-04-02", "name": "02.04.2026"}],
                "metrics": [389100.00, 27, 4890],
            },
            {
                "dimensions": [{"id": "2026-04-03", "name": "03.04.2026"}],
                "metrics": [512300.00, 38, 6340],
            },
        ],
        "totals": [2154350.00, 150, 26880],
    },
    "timestamp": "2026-04-04T10:00:00Z",
}

FINANCE_REPORT_RESPONSE = {
    "result": {
        "operations": [
            {
                "operation_date": "2026-04-03T00:00:00Z",
                "operation_type": "OperationAgentDeliveredToCustomer",
                "posting_number": "89721045-0010-1",
                "items": [
                    {
                        "name": "Наушники Apple AirPods Pro 2 (USB-C), белый",
                        "sku": 987210451,
                    }
                ],
                "accruals_for_sale": 18990.00,
                "sale_commission": -2848.50,
                "amount": 16141.50,
            },
            {
                "operation_date": "2026-04-02T00:00:00Z",
                "operation_type": "OperationAgentDeliveredToCustomer",
                "posting_number": "FBO-78412690-0001",
                "items": [
                    {
                        "name": "Пылесос Dyson V15 Detect Absolute, золотой",
                        "sku": 987210452,
                    }
                ],
                "accruals_for_sale": 54990.00,
                "sale_commission": -8248.50,
                "amount": 46741.50,
            },
        ],
        "page_count": 1,
        "row_count": 2,
    }
}

CREATE_PRODUCT_RESPONSE = {
    "result": {
        "task_id": 348901562,
        "product_id": 0,
    }
}


@pytest.fixture()
def mock_app_context(
    test_settings: Settings,
    mock_ozon_client: AsyncMock,
    mock_cache: RedisCache,
    mock_rate_limiter: RateLimiter,
    mock_audit: AsyncMock,
) -> Any:
    """AppContext assembled from mock components."""
    from ozon_mcp_server.server import AppContext

    return AppContext(
        settings=test_settings,
        ozon=mock_ozon_client,
        cache=mock_cache,
        rate_limiter=mock_rate_limiter,
        audit=mock_audit,
        db=MagicMock(),
    )


@pytest.fixture()
def mock_ctx(mock_app_context: Any) -> MagicMock:
    """Mock MCP Context with AppContext in lifespan_context."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context = mock_app_context
    return ctx
