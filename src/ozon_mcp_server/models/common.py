"""
Shared models: errors, pagination, base responses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OzonErrorResponse(BaseModel):
    """Standard Ozon API error response."""

    code: int = Field(default=0)
    message: str = Field(default="")
    details: list[dict[str, Any]] = Field(default_factory=list)


class PaginationParams(BaseModel):
    """Base pagination parameters."""

    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ToolResult(BaseModel):
    """Wrapper for tool results ensuring uniform response shape."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    cached: bool = False
    response_time_ms: float = 0.0

    @classmethod
    def ok(cls, data: dict[str, Any], cached: bool = False, ms: float = 0.0) -> ToolResult:
        return cls(success=True, data=data, cached=cached, response_time_ms=ms)

    @classmethod
    def fail(cls, error: str, ms: float = 0.0) -> ToolResult:
        return cls(success=False, error=error, response_time_ms=ms)
