"""
MCP tools for Ozon Seller API order and analytics operations.

Read-only: get_fbs_orders, get_fbo_orders, get_analytics, get_finance_report, get_warehouse_list
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server.fastmcp import Context

from ozon_mcp_server.models.orders import (
    GetAnalyticsParams,
    GetFinanceParams,
    GetOrderListParams,
)
from ozon_mcp_server.server import get_app_context, mcp


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_fbs_orders(
    status: str = "awaiting_packaging",
    days_back: int = 7,
    limit: int = 50,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List FBS orders (Fulfillment by Seller) for a given period.

    FBS means the seller handles packaging and shipping (similar to FBM on Amazon).
    Returns: order number, items, status, delivery address.

    Args:
        status: Order status filter (awaiting_packaging, delivering, delivered, cancelled)
        days_back: How many days back to search (1-90)
        limit: Max number of orders (1-1000)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = GetOrderListParams(
        status=status, days_back=days_back, limit=limit,  # type: ignore[arg-type]
    )

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=params.days_back)).strftime("%Y-%m-%dT00:00:00Z")
    to = now.strftime("%Y-%m-%dT23:59:59Z")

    payload = {
        "filter": {
            "status": params.status,
            "since": since,
            "to": to,
        },
        "limit": params.limit,
        "offset": params.offset,
        "with": {
            "analytics_data": True,
            "financial_data": True,
        },
    }

    cache_params = {"status": params.status, "days": params.days_back, "limit": params.limit}
    cached = await app.cache.get("fbs_orders", cache_params)
    if cached:
        await app.audit.log("get_fbs_orders", cache_params, "success", 0)
        return cached

    result = await app.ozon.request("/v3/posting/fbs/list", payload)
    elapsed = (time.monotonic() - start) * 1000

    # Short TTL — orders change frequently
    await app.cache.set("fbs_orders", cache_params, result, ttl=120)
    await app.audit.log("get_fbs_orders", cache_params, "success", elapsed)

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_fbo_orders(
    status: str = "awaiting_packaging",
    days_back: int = 7,
    limit: int = 50,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List FBO orders (Fulfillment by Ozon) for a given period.

    FBO means inventory is stored at Ozon's warehouse (similar to FBA on Amazon).

    Args:
        status: Order status filter
        days_back: How many days back to search (1-90)
        limit: Max number of orders (1-1000)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = GetOrderListParams(
        status=status, days_back=days_back, limit=limit,  # type: ignore[arg-type]
    )

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=params.days_back)).strftime("%Y-%m-%dT00:00:00Z")
    to = now.strftime("%Y-%m-%dT23:59:59Z")

    payload = {
        "filter": {
            "status": params.status,
            "since": since,
            "to": to,
        },
        "limit": params.limit,
        "offset": params.offset,
    }

    result = await app.ozon.request("/v2/posting/fbo/list", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.audit.log("get_fbo_orders", {"status": params.status}, "success", elapsed)
    return result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_analytics(
    date_from: str = "",
    date_to: str = "",
    metrics: list[str] | None = None,
    dimensions: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get sales analytics from Ozon.

    Metrics: revenue, ordered_units (orders), hits_view (views),
    conv_tocart (add-to-cart conversion), returns.

    Args:
        date_from: Start date (YYYY-MM-DD, required)
        date_to: End date (YYYY-MM-DD, required)
        metrics: Metrics to request (revenue, ordered_units, hits_view, etc.)
        dimensions: Grouping dimensions (day, week, month, sku, category1...)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    if not date_from or not date_to:
        return {"error": "Provide date_from and date_to in YYYY-MM-DD format"}

    params = GetAnalyticsParams(
        date_from=date_from,
        date_to=date_to,
        metrics=metrics or ["revenue", "ordered_units", "hits_view"],  # type: ignore[arg-type]
        dimensions=dimensions or ["day"],  # type: ignore[arg-type]
    )

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    # Analytics cached longer (30 minutes)
    cache_params = params.model_dump()
    cached = await app.cache.get("analytics", cache_params)
    if cached:
        await app.audit.log("get_analytics", cache_params, "success", 0)
        return cached

    payload = {
        "date_from": params.date_from,
        "date_to": params.date_to,
        "metrics": list(params.metrics),
        "dimension": list(params.dimensions),
        "limit": params.limit,
        "offset": params.offset,
    }

    result = await app.ozon.request("/v1/analytics/data", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.set("analytics", cache_params, result, ttl=1800)
    await app.audit.log("get_analytics", cache_params, "success", elapsed)

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_finance_report(
    date_from: str = "",
    date_to: str = "",
    page: int = 1,
    page_size: int = 50,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get financial transactions from Ozon.

    Returns: accruals, deductions, commissions, penalties for a given period.

    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        page: Page number
        page_size: Page size (1-1000)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    if not date_from or not date_to:
        return {"error": "Provide date_from and date_to in YYYY-MM-DD format"}

    params = GetFinanceParams(
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    payload = {
        "filter": {
            "date": {
                "from": f"{params.date_from}T00:00:00.000Z",
                "to": f"{params.date_to}T23:59:59.999Z",
            },
            "transaction_type": params.transaction_type,
        },
        "page": params.page,
        "page_size": params.page_size,
    }

    result = await app.ozon.request("/v3/finance/transaction/list", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.audit.log("get_finance_report", {"from": date_from, "to": date_to}, "success", elapsed)
    return result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_warehouse_list(ctx: Context | None = None) -> dict[str, Any]:
    """List all seller warehouses (FBS + FBO).

    Returns: warehouse ID, name, type, status.
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    # Warehouse list cached for 1 hour (rarely changes)
    cached = await app.cache.get("warehouses", {})
    if cached:
        return cached

    result = await app.ozon.request("/v1/warehouse/list")
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.set("warehouses", {}, result, ttl=3600)
    await app.audit.log("get_warehouse_list", {}, "success", elapsed)

    return result
