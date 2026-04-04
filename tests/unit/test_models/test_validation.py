"""Tests for Pydantic model validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ozon_mcp_server.models.orders import GetAnalyticsParams, GetOrderListParams
from ozon_mcp_server.models.products import (
    GetProductInfoParams,
    GetProductListParams,
    UpdatePricesParams,
    UpdateStocksParams,
)


class TestGetProductListParams:
    def test_defaults(self) -> None:
        p = GetProductListParams()
        assert p.limit == 100
        assert p.visibility == "ALL"
        assert p.last_id == ""

    def test_valid_visibility(self) -> None:
        p = GetProductListParams(visibility="ARCHIVED")
        assert p.visibility == "ARCHIVED"

    def test_invalid_visibility(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(visibility="HACKED")  # type: ignore[arg-type]

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(limit=0)
        with pytest.raises(ValidationError):
            GetProductListParams(limit=1001)

    def test_valid_limit(self) -> None:
        p = GetProductListParams(limit=500)
        assert p.limit == 500

    def test_offer_ids_validation(self) -> None:
        p = GetProductListParams(offer_ids=["SKU-001", "sku_002"])
        assert len(p.offer_ids) == 2

    def test_offer_ids_injection_blocked(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(offer_ids=["'; DROP TABLE--"])

    def test_last_id_injection_blocked(self) -> None:
        with pytest.raises(ValidationError):
            GetProductListParams(last_id="../../../etc/passwd")


class TestGetProductInfoParams:
    def test_at_least_one_id(self) -> None:
        p = GetProductInfoParams(product_id=123)
        assert p.product_id == 123

    def test_offer_id_valid(self) -> None:
        p = GetProductInfoParams(offer_id="SKU-001")
        assert p.offer_id == "SKU-001"

    def test_offer_id_injection(self) -> None:
        with pytest.raises(ValidationError):
            GetProductInfoParams(offer_id="<script>alert(1)</script>")


class TestUpdatePricesParams:
    def test_valid_price_update(self) -> None:
        p = UpdatePricesParams(prices=[
            {"product_id": 123, "price": "1999.00"},
        ])
        assert len(p.prices) == 1
        assert p.prices[0].price == "1999.00"

    def test_price_format_validation(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePricesParams(prices=[
                {"product_id": 123, "price": "-100"},  # negative
            ])

    def test_price_sql_injection(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePricesParams(prices=[
                {"product_id": 123, "price": "100; DROP TABLE"},
            ])

    def test_empty_prices_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePricesParams(prices=[])

    def test_max_prices_limit(self) -> None:
        prices = [{"product_id": i, "price": "100.00"} for i in range(1001)]
        with pytest.raises(ValidationError):
            UpdatePricesParams(prices=prices)


class TestUpdateStocksParams:
    def test_valid_stock(self) -> None:
        p = UpdateStocksParams(stocks=[
            {"product_id": 123, "stock": 50, "warehouse_id": 1},
        ])
        assert p.stocks[0].stock == 50

    def test_negative_stock_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStocksParams(stocks=[
                {"product_id": 123, "stock": -1, "warehouse_id": 1},
            ])

    def test_stock_overflow_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStocksParams(stocks=[
                {"product_id": 123, "stock": 1_000_000, "warehouse_id": 1},
            ])


class TestGetOrderListParams:
    def test_defaults(self) -> None:
        p = GetOrderListParams()
        assert p.status == "awaiting_packaging"
        assert p.days_back == 7

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            GetOrderListParams(status="hacked")  # type: ignore[arg-type]

    def test_days_back_bounds(self) -> None:
        with pytest.raises(ValidationError):
            GetOrderListParams(days_back=0)
        with pytest.raises(ValidationError):
            GetOrderListParams(days_back=91)


class TestGetAnalyticsParams:
    def test_valid_dates(self) -> None:
        p = GetAnalyticsParams(date_from="2026-04-01", date_to="2026-04-04")
        assert p.date_from == "2026-04-01"

    def test_invalid_date_format(self) -> None:
        with pytest.raises(ValidationError):
            GetAnalyticsParams(date_from="04/01/2026", date_to="04/04/2026")

    def test_date_injection(self) -> None:
        with pytest.raises(ValidationError):
            GetAnalyticsParams(date_from="2026-04-01; DROP TABLE", date_to="2026-04-04")

    def test_invalid_metric(self) -> None:
        with pytest.raises(ValidationError):
            GetAnalyticsParams(
                date_from="2026-04-01", date_to="2026-04-04",
                metrics=["hacked_metric"],  # type: ignore[list-item]
            )
