"""
Validation models for product tools.

Strict typing, allowlists for enumerations, length and range constraints.
Every parameter is a potential attack entry point — validation is mandatory.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# Allowed product visibility values (allowlist)
ProductVisibility = Literal[
    "ALL",
    "VISIBLE",
    "INVISIBLE",
    "EMPTY_STOCK",
    "NOT_MODERATED",
    "MODERATED",
    "DISABLED",
    "STATE_FAILED",
    "READY_TO_SUPPLY",
    "VALIDATION_STATE_PENDING",
    "VALIDATION_STATE_FAIL",
    "VALIDATION_STATE_SUCCESS",
    "TO_SUPPLY",
    "IN_SALE",
    "REMOVED_FROM_SALE",
    "BAN_NOT_CONFIRMED",
    "OVERPRICED",
    "CRITICALLY_OVERPRICED",
    "EMPTY_BARCODE",
    "BARCODE_EXISTS",
    "QUARANTINE",
    "ARCHIVED",
    "OVERPRICED_WITH_STOCK",
    "PARTIAL_APPROVED",
    "IMAGE_ABSENT",
    "MODERATION_BLOCK",
]


class GetProductListParams(BaseModel):
    """Parameters for fetching the product list."""

    limit: int = Field(default=100, ge=1, le=1000, description="Number of products to return")
    last_id: str = Field(
        default="", max_length=64, description="Pagination cursor from previous response"
    )
    visibility: ProductVisibility = Field(
        default="ALL", description="Visibility filter"
    )
    offer_ids: list[str] = Field(
        default_factory=list, max_length=1000,
        description="Filter by seller SKUs (offer IDs)",
    )
    product_ids: list[int] = Field(
        default_factory=list, max_length=1000,
        description="Filter by Ozon product IDs",
    )

    @field_validator("offer_ids", mode="before")
    @classmethod
    def validate_offer_ids(cls, v: list[str]) -> list[str]:
        for oid in v:
            if not re.match(r"^[a-zA-Z0-9_\-\.]{1,64}$", str(oid)):
                msg = f"Invalid offer_id: {oid!r}"
                raise ValueError(msg)
        return v

    @field_validator("last_id")
    @classmethod
    def validate_last_id(cls, v: str) -> str:
        if v and not re.match(r"^[a-zA-Z0-9_\-]{0,64}$", v):
            msg = f"Invalid last_id: {v!r}"
            raise ValueError(msg)
        return v


class GetProductInfoParams(BaseModel):
    """Parameters for fetching product details."""

    product_id: int = Field(default=0, ge=0, description="Ozon product ID")
    offer_id: str = Field(default="", max_length=64, description="Seller SKU (offer ID)")
    sku: int = Field(default=0, ge=0, description="Product SKU")

    @field_validator("offer_id")
    @classmethod
    def validate_offer_id(cls, v: str) -> str:
        if v and not re.match(r"^[a-zA-Z0-9_\-\.]{1,64}$", v):
            msg = f"Invalid offer_id: {v!r}"
            raise ValueError(msg)
        return v


class PriceUpdate(BaseModel):
    """Price update for a single product."""

    product_id: int = Field(..., gt=0, description="Product ID")
    price: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$", description="New price")
    old_price: str = Field(
        default="0",
        pattern=r"^\d+(\.\d{1,2})?$",
        description="Old price (strikethrough display)",
    )
    min_price: str = Field(
        default="0",
        pattern=r"^\d+(\.\d{1,2})?$",
        description="Minimum price for auto-strategies",
    )


class UpdatePricesParams(BaseModel):
    """Parameters for bulk price update."""

    prices: list[PriceUpdate] = Field(
        ..., min_length=1, max_length=1000,
        description="List of price updates (max 1000)",
    )


class StockUpdate(BaseModel):
    """Stock update for a single product at a warehouse."""

    product_id: int = Field(..., gt=0, description="Product ID")
    stock: int = Field(..., ge=0, le=999999, description="Quantity in stock")
    warehouse_id: int = Field(..., gt=0, description="Warehouse ID")


class UpdateStocksParams(BaseModel):
    """Parameters for bulk stock update."""

    stocks: list[StockUpdate] = Field(
        ..., min_length=1, max_length=100,
        description="List of stock updates (max 100 per request)",
    )


class ArchiveProductParams(BaseModel):
    """Parameters for archiving products."""

    product_ids: list[int] = Field(
        ..., min_length=1, max_length=100,
        description="List of product IDs to archive (max 100)",
    )

    @field_validator("product_ids", mode="before")
    @classmethod
    def validate_product_ids(cls, v: list[int]) -> list[int]:
        for pid in v:
            if not isinstance(pid, int) or pid <= 0:
                msg = f"Invalid product_id: {pid!r} (must be positive integer)"
                raise ValueError(msg)
        return v


class CreateProductParams(BaseModel):
    """Parameters for creating a new product on Ozon."""

    name: str = Field(
        ..., min_length=1, max_length=500,
        description="Product name",
    )
    offer_id: str = Field(
        ..., min_length=1, max_length=64,
        description="Seller SKU (unique identifier in your system)",
    )
    category_id: int = Field(
        ..., gt=0,
        description="Ozon category ID",
    )
    price: str = Field(
        ..., pattern=r"^\d+(\.\d{1,2})?$",
        description="Product price (e.g., '1999.00')",
    )
    vat: str = Field(
        default="0",
        description="VAT rate: 0, 0.1, or 0.2",
    )
    weight: int = Field(
        ..., gt=0, le=1000000,
        description="Weight in grams",
    )
    width: int = Field(
        ..., gt=0, le=1000000,
        description="Width in millimeters",
    )
    height: int = Field(
        ..., gt=0, le=1000000,
        description="Height in millimeters",
    )
    depth: int = Field(
        ..., gt=0, le=1000000,
        description="Depth in millimeters",
    )
    images: list[str] = Field(
        default_factory=list, max_length=15,
        description="Image URLs (HTTPS only, max 15)",
    )
    description: str = Field(
        default="", max_length=6000,
        description="Product description (max 6000 chars)",
    )

    @field_validator("offer_id")
    @classmethod
    def validate_offer_id(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_\-\.]{1,64}$", v):
            msg = f"Invalid offer_id: {v!r}"
            raise ValueError(msg)
        return v

    @field_validator("vat")
    @classmethod
    def validate_vat(cls, v: str) -> str:
        allowed = {"0", "0.1", "0.2"}
        if v not in allowed:
            msg = f"VAT must be one of {allowed} (got: {v!r})"
            raise ValueError(msg)
        return v

    @field_validator("images", mode="before")
    @classmethod
    def validate_images(cls, v: list[str]) -> list[str]:
        for url in v:
            if not str(url).startswith("https://"):
                msg = f"Image URL must use HTTPS: {url!r}"
                raise ValueError(msg)
        return v


class GetStockParams(BaseModel):
    """Parameters for fetching stock levels on warehouses."""

    product_ids: list[int] = Field(
        default_factory=list, max_length=100,
        description="Filter by product IDs",
    )
    offer_ids: list[str] = Field(
        default_factory=list, max_length=100,
        description="Filter by seller SKUs (offer IDs)",
    )

    @field_validator("offer_ids", mode="before")
    @classmethod
    def validate_offer_ids(cls, v: list[str]) -> list[str]:
        for oid in v:
            if not re.match(r"^[a-zA-Z0-9_\-\.]{1,64}$", str(oid)):
                msg = f"Invalid offer_id: {oid!r}"
                raise ValueError(msg)
        return v
