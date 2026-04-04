"""Extended tests for product model validators (CreateProductParams, ArchiveProductParams, GetStockParams)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ozon_mcp_server.models.products import (
    ArchiveProductParams,
    CreateProductParams,
    GetStockParams,
)


class TestCreateProductParams:
    def test_valid(self):
        p = CreateProductParams(
            name="Наушники Sony WH-1000XM5",
            offer_id="WH-SONY-XM5",
            category_id=15621031,
            price="29990.00",
            weight=250,
            width=200,
            height=250,
            depth=50,
        )
        assert p.name == "Наушники Sony WH-1000XM5"
        assert p.vat == "0"
        assert p.images == []

    def test_invalid_offer_id(self):
        with pytest.raises(ValidationError):
            CreateProductParams(
                name="Test",
                offer_id="SKU; DROP TABLE",
                category_id=100,
                price="999.00",
                weight=100,
                width=100,
                height=100,
                depth=100,
            )

    def test_invalid_vat(self):
        with pytest.raises(ValidationError):
            CreateProductParams(
                name="Test",
                offer_id="TEST-001",
                category_id=100,
                price="999.00",
                vat="0.5",
                weight=100,
                width=100,
                height=100,
                depth=100,
            )

    def test_valid_vat_values(self):
        for vat_val in ("0", "0.1", "0.2"):
            p = CreateProductParams(
                name="Test",
                offer_id="TEST-001",
                category_id=100,
                price="999.00",
                vat=vat_val,
                weight=100,
                width=100,
                height=100,
                depth=100,
            )
            assert p.vat == vat_val

    def test_http_image_rejected(self):
        with pytest.raises(ValidationError):
            CreateProductParams(
                name="Test",
                offer_id="TEST-001",
                category_id=100,
                price="999.00",
                weight=100,
                width=100,
                height=100,
                depth=100,
                images=["http://insecure.com/img.jpg"],
            )

    def test_https_image_accepted(self):
        p = CreateProductParams(
            name="Test",
            offer_id="TEST-001",
            category_id=100,
            price="999.00",
            weight=100,
            width=100,
            height=100,
            depth=100,
            images=["https://cdn.example.com/img.jpg"],
        )
        assert len(p.images) == 1

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            CreateProductParams(
                name="",
                offer_id="TEST-001",
                category_id=100,
                price="999.00",
                weight=100,
                width=100,
                height=100,
                depth=100,
            )

    def test_zero_weight_rejected(self):
        with pytest.raises(ValidationError):
            CreateProductParams(
                name="Test",
                offer_id="TEST-001",
                category_id=100,
                price="999.00",
                weight=0,
                width=100,
                height=100,
                depth=100,
            )


class TestArchiveProductParams:
    def test_valid(self):
        p = ArchiveProductParams(product_ids=[1, 2, 3])
        assert p.product_ids == [1, 2, 3]

    def test_empty_list_rejected(self):
        with pytest.raises(ValidationError):
            ArchiveProductParams(product_ids=[])

    def test_negative_id_rejected(self):
        with pytest.raises(ValidationError):
            ArchiveProductParams(product_ids=[-1])

    def test_zero_id_rejected(self):
        with pytest.raises(ValidationError):
            ArchiveProductParams(product_ids=[0])


class TestGetStockParams:
    def test_valid_offer_ids(self):
        p = GetStockParams(offer_ids=["WH-AIRPODS-PRO-2"])
        assert p.offer_ids == ["WH-AIRPODS-PRO-2"]

    def test_invalid_offer_ids(self):
        with pytest.raises(ValidationError):
            GetStockParams(offer_ids=["SKU; DROP TABLE"])

    def test_valid_product_ids(self):
        p = GetStockParams(product_ids=[987210451])
        assert p.product_ids == [987210451]
