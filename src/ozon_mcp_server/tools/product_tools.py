"""
MCP tools for Ozon Seller API product operations.

Read-only: get_product_list, get_product_info, get_stock_on_warehouses
Write (destructive): update_prices, update_stocks, archive_product, create_product
"""

from __future__ import annotations

import time
from typing import Any

from mcp.server.fastmcp import Context

from ozon_mcp_server.models.products import (
    ArchiveProductParams,
    CreateProductParams,
    GetProductInfoParams,
    GetProductListParams,
    GetStockParams,
    UpdatePricesParams,
    UpdateStocksParams,
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
async def get_product_list(
    limit: int = 100,
    last_id: str = "",
    visibility: str = "ALL",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List products in the Ozon seller store.

    Returns product IDs and offer_ids with pagination support.
    Filter by visibility: ALL, VISIBLE, INVISIBLE, ARCHIVED, etc.

    Args:
        limit: Number of products to return (1-1000, default 100)
        last_id: Pagination cursor from previous response
        visibility: Visibility filter (ALL, VISIBLE, INVISIBLE, ARCHIVED...)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = GetProductListParams(
        limit=limit, last_id=last_id, visibility=visibility,  # type: ignore[arg-type]
    )

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    cache_params = params.model_dump()
    cached = await app.cache.get("products_list", cache_params)
    if cached:
        await app.audit.log("get_product_list", cache_params, "success", 0)
        return cached

    payload: dict[str, Any] = {
        "filter": {"visibility": params.visibility},
        "limit": params.limit,
    }
    if params.last_id:
        payload["last_id"] = params.last_id
    if params.offer_ids:
        payload["filter"]["offer_id"] = params.offer_ids
    if params.product_ids:
        payload["filter"]["product_id"] = params.product_ids

    result = await app.ozon.request("/v2/product/list", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.set("products_list", cache_params, result, ttl=300)
    await app.audit.log("get_product_list", cache_params, "success", elapsed)

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_product_info(
    product_id: int = 0,
    offer_id: str = "",
    sku: int = 0,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get detailed information about a product on Ozon.

    Provide at least one identifier: product_id, offer_id, or sku.
    Returns: name, description, prices, stock levels, category, rating.

    Args:
        product_id: Ozon product ID (number)
        offer_id: Seller SKU (string)
        sku: Product SKU (number)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = GetProductInfoParams(
        product_id=product_id, offer_id=offer_id, sku=sku,
    )

    if not any([params.product_id, params.offer_id, params.sku]):
        return {"error": "Provide at least one: product_id, offer_id, or sku"}

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    payload: dict[str, Any] = {}
    if params.product_id:
        payload["product_id"] = params.product_id
    if params.offer_id:
        payload["offer_id"] = params.offer_id
    if params.sku:
        payload["sku"] = params.sku

    cached = await app.cache.get("product_info", payload)
    if cached:
        await app.audit.log("get_product_info", payload, "success", 0)
        return cached

    result = await app.ozon.request("/v2/product/info", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.set("product_info", payload, result, ttl=300)
    await app.audit.log("get_product_info", payload, "success", elapsed)

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_stock_on_warehouses(
    product_ids: list[int] | None = None,
    offer_ids: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get current stock levels across all warehouses.

    Provide product_ids or offer_ids to filter results.
    Returns: product ID, warehouse ID, stock quantity, reserved quantity.

    Args:
        product_ids: Filter by Ozon product IDs (max 100)
        offer_ids: Filter by seller SKUs (max 100)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = GetStockParams(
        product_ids=product_ids or [],
        offer_ids=offer_ids or [],
    )

    if not params.product_ids and not params.offer_ids:
        return {"error": "Provide at least one: product_ids or offer_ids"}

    await app.rate_limiter.check_global(app.settings.rate_limit_rpm)

    payload: dict[str, Any] = {"filter": {}}
    if params.product_ids:
        payload["filter"]["product_id"] = params.product_ids
    if params.offer_ids:
        payload["filter"]["offer_id"] = params.offer_ids

    cache_params = {"product_ids": params.product_ids, "offer_ids": params.offer_ids}
    cached = await app.cache.get("stock_info", cache_params)
    if cached:
        await app.audit.log("get_stock_on_warehouses", cache_params, "success", 0)
        return cached

    result = await app.ozon.request("/v1/product/info/stocks", payload)
    elapsed = (time.monotonic() - start) * 1000

    # Short TTL — stock levels change frequently
    await app.cache.set("stock_info", cache_params, result, ttl=120)
    await app.audit.log("get_stock_on_warehouses", cache_params, "success", elapsed)

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def update_prices(
    prices: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update product prices on Ozon.

    WARNING: Destructive operation — changes real prices in the store!
    Each item must contain product_id and price.

    Args:
        prices: List of price updates. Each item:
            - product_id (int): Product ID
            - price (str): New price (e.g., "1999.00")
            - old_price (str, optional): Strikethrough price
            - min_price (str, optional): Min price for auto-strategies
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = UpdatePricesParams(prices=prices)  # type: ignore[arg-type]

    await app.rate_limiter.check_write(app.settings.rate_limit_write_rpm)

    payload = {"prices": [p.model_dump() for p in params.prices]}
    result = await app.ozon.request("/v1/product/import/prices", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.invalidate("products_list")
    await app.cache.invalidate("product_info")

    await app.audit.log(
        "update_prices",
        {"count": len(params.prices), "product_ids": [p.product_id for p in params.prices]},
        "success",
        elapsed,
    )

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def update_stocks(
    stocks: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update product stock levels at warehouses.

    WARNING: Destructive operation — changes real stock quantities!
    Max 100 products per request. Rate limit: 10 req/min.

    Args:
        stocks: List of stock updates. Each item:
            - product_id (int): Product ID
            - stock (int): Quantity in stock (0-999999)
            - warehouse_id (int): Warehouse ID
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = UpdateStocksParams(stocks=stocks)  # type: ignore[arg-type]

    await app.rate_limiter.check_write(app.settings.rate_limit_write_rpm)

    payload = {
        "stocks": [
            {
                "product_id": s.product_id,
                "stock": s.stock,
                "warehouse_id": s.warehouse_id,
            }
            for s in params.stocks
        ]
    }
    result = await app.ozon.request("/v2/products/stocks", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.invalidate("products_list")
    await app.cache.invalidate("product_info")
    await app.cache.invalidate("stock_info")

    await app.audit.log(
        "update_stocks",
        {"count": len(params.stocks)},
        "success",
        elapsed,
    )

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def archive_product(
    product_ids: list[int],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Archive products on Ozon (remove from active listings).

    WARNING: Destructive operation — archived products are no longer visible to buyers!
    Products can be unarchived later. Max 100 products per request.

    Args:
        product_ids: List of product IDs to archive (max 100)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = ArchiveProductParams(product_ids=product_ids)

    await app.rate_limiter.check_write(app.settings.rate_limit_write_rpm)

    payload = {"product_id": params.product_ids}
    result = await app.ozon.request("/v1/product/archive", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.invalidate("products_list")
    await app.cache.invalidate("product_info")

    await app.audit.log(
        "archive_product",
        {"count": len(params.product_ids), "product_ids": params.product_ids},
        "success",
        elapsed,
    )

    return result


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def create_product(
    name: str,
    offer_id: str,
    category_id: int,
    price: str,
    weight: int,
    width: int,
    height: int,
    depth: int,
    description: str = "",
    vat: str = "0",
    images: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new product listing on Ozon.

    WARNING: Creates a real product in the store! Requires moderation before going live.
    Weight is in grams, dimensions in millimeters.

    Args:
        name: Product name (1-500 chars)
        offer_id: Seller SKU — unique identifier in your system
        category_id: Ozon category ID (from category tree)
        price: Product price (e.g., "1999.00")
        weight: Weight in grams
        width: Width in millimeters
        height: Height in millimeters
        depth: Depth in millimeters
        description: Product description (max 6000 chars)
        vat: VAT rate: "0", "0.1", or "0.2"
        images: Image URLs (HTTPS only, max 15)
    """
    assert ctx is not None
    app = get_app_context(ctx)
    start = time.monotonic()

    params = CreateProductParams(
        name=name,
        offer_id=offer_id,
        category_id=category_id,
        price=price,
        weight=weight,
        width=width,
        height=height,
        depth=depth,
        description=description,
        vat=vat,
        images=images or [],
    )

    await app.rate_limiter.check_write(app.settings.rate_limit_write_rpm)

    payload = {
        "items": [
            {
                "name": params.name,
                "offer_id": params.offer_id,
                "category_id": params.category_id,
                "price": params.price,
                "vat": params.vat,
                "weight": params.weight,
                "weight_unit": "g",
                "width": params.width,
                "height": params.height,
                "depth": params.depth,
                "dimension_unit": "mm",
                "images": [{"file_name": url, "default": i == 0} for i, url in enumerate(params.images)],
                "description": params.description,
            }
        ]
    }

    result = await app.ozon.request("/v3/product/import", payload)
    elapsed = (time.monotonic() - start) * 1000

    await app.cache.invalidate("products_list")

    await app.audit.log(
        "create_product",
        {"offer_id": params.offer_id, "name": params.name[:50]},
        "success",
        elapsed,
    )

    return result
