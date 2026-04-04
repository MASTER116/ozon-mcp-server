"""Tests for shared models (common.py)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ozon_mcp_server.models.common import OzonErrorResponse, PaginationParams, ToolResult


class TestOzonErrorResponse:
    def test_defaults(self):
        err = OzonErrorResponse()
        assert err.code == 0
        assert err.message == ""
        assert err.details == []

    def test_with_values(self):
        err = OzonErrorResponse(code=400, message="Bad Request", details=[{"field": "name"}])
        assert err.code == 400
        assert err.message == "Bad Request"
        assert err.details == [{"field": "name"}]


class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams()
        assert p.limit == 100
        assert p.offset == 0

    def test_valid(self):
        p = PaginationParams(limit=50, offset=10)
        assert p.limit == 50
        assert p.offset == 10

    def test_limit_zero_rejected(self):
        with pytest.raises(ValidationError):
            PaginationParams(limit=0)

    def test_limit_overflow_rejected(self):
        with pytest.raises(ValidationError):
            PaginationParams(limit=1001)

    def test_negative_offset_rejected(self):
        with pytest.raises(ValidationError):
            PaginationParams(offset=-1)


class TestToolResult:
    def test_ok(self):
        r = ToolResult.ok({"items": [1, 2]}, cached=True, ms=5.3)
        assert r.success is True
        assert r.data == {"items": [1, 2]}
        assert r.cached is True
        assert r.response_time_ms == 5.3
        assert r.error is None

    def test_fail(self):
        r = ToolResult.fail("something broke", ms=1.2)
        assert r.success is False
        assert r.error == "something broke"
        assert r.data is None
        assert r.response_time_ms == 1.2

    def test_default_fields(self):
        r = ToolResult(success=True)
        assert r.cached is False
        assert r.response_time_ms == 0.0
