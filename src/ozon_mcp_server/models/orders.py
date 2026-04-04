"""
Validation models for order and analytics tools.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# Allowed FBS order statuses
FBSStatus = Literal[
    "awaiting_registration",
    "acceptance_in_progress",
    "awaiting_approve",
    "awaiting_packaging",
    "awaiting_deliver",
    "arbitration",
    "client_arbitration",
    "delivering",
    "driver_pickup",
    "delivered",
    "cancelled",
    "not_accepted",
    "sent_by_seller",
]

# Allowed analytics metrics
AnalyticsMetric = Literal[
    "revenue",
    "ordered_units",
    "hits_view_search",
    "hits_view_pdp",
    "hits_view",
    "hits_tocart_search",
    "hits_tocart_pdp",
    "hits_tocart",
    "session_view_search",
    "session_view_pdp",
    "session_view",
    "conv_tocart_search",
    "conv_tocart_pdp",
    "conv_tocart",
    "returns",
    "cancellations",
    "delivered_units",
    "position_category",
]

AnalyticsDimension = Literal[
    "sku", "spu", "day", "week", "month", "year", "category1",
    "category2", "category3", "category4", "brand", "modelID",
]


class GetOrderListParams(BaseModel):
    """Parameters for fetching FBS order list."""

    status: FBSStatus = Field(
        default="awaiting_packaging",
        description="Order status filter",
    )
    days_back: int = Field(
        default=7, ge=1, le=90,
        description="Number of days to look back",
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Max number of orders")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class GetAnalyticsParams(BaseModel):
    """Parameters for fetching sales analytics."""

    date_from: str = Field(
        ..., description="Start date (YYYY-MM-DD)"
    )
    date_to: str = Field(
        ..., description="End date (YYYY-MM-DD)"
    )
    metrics: list[AnalyticsMetric] = Field(
        default=["revenue", "ordered_units", "hits_view"],
        min_length=1, max_length=14,
        description="Metrics to request",
    )
    dimensions: list[AnalyticsDimension] = Field(
        default=["day"],
        min_length=1, max_length=3,
        description="Dimensions (grouping)",
    )
    limit: int = Field(default=1000, ge=1, le=1000, description="Row limit")
    offset: int = Field(default=0, ge=0, description="Offset")

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            msg = f"Date format must be YYYY-MM-DD (got: {v!r})"
            raise ValueError(msg)
        return v


class GetFinanceParams(BaseModel):
    """Parameters for fetching financial transactions."""

    date_from: str = Field(..., description="Start date (YYYY-MM-DD)")
    date_to: str = Field(..., description="End date (YYYY-MM-DD)")
    transaction_type: str = Field(
        default="all",
        description="Transaction type (all, orders, returns, services, etc.)",
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=1000, description="Page size")

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            msg = f"Date format must be YYYY-MM-DD (got: {v!r})"
            raise ValueError(msg)
        return v
