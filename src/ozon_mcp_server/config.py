"""
Application configuration.

All secrets are stored as SecretStr — masked in logs, repr(), and tracebacks.
Values are loaded from environment variables or a .env file.
"""

from __future__ import annotations

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP server settings for Ozon Seller API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Ozon API ---
    ozon_client_id: str = Field(
        ..., description="Ozon Seller Client-Id (from seller dashboard)"
    )
    ozon_api_key: SecretStr = Field(
        ..., description="Ozon Seller API Key (180-day expiry)"
    )
    ozon_api_base_url: str = Field(
        default="https://api-seller.ozon.ru",
        description="Ozon Seller API base URL (do not change — SSRF protection)",
    )

    # --- MCP Auth ---
    mcp_auth_token: SecretStr = Field(
        default=SecretStr(""),
        description="Bearer token for MCP client authentication (empty = auth disabled)",
    )

    # --- Redis ---
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    cache_ttl_seconds: int = Field(
        default=300, ge=0, le=86400,
        description="Default cache TTL in seconds",
    )

    # --- PostgreSQL ---
    postgres_dsn: SecretStr = Field(
        default=SecretStr("postgresql://ozon:secret@localhost:5432/ozon_mcp"),
        description="PostgreSQL connection DSN",
    )

    # --- Rate Limiting ---
    rate_limit_rpm: int = Field(
        default=100, ge=1, le=1000,
        description="Max requests to Ozon API per minute (global)",
    )
    rate_limit_write_rpm: int = Field(
        default=10, ge=1, le=100,
        description="Max write requests to Ozon API per minute",
    )

    # --- Circuit Breaker ---
    circuit_breaker_threshold: int = Field(
        default=5, ge=1, le=50,
        description="Consecutive failures before circuit opens",
    )
    circuit_breaker_recovery_seconds: float = Field(
        default=60.0, ge=5.0, le=600.0,
        description="Seconds before circuit transitions from open to half-open",
    )

    # --- Server ---
    server_name: str = Field(
        default="Ozon Seller MCP Server",
        description="MCP server name",
    )
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR)",
    )
    transport: str = Field(
        default="stdio",
        description="MCP transport: stdio | streamable-http | sse",
    )
    port: int = Field(
        default=8000, ge=1024, le=65535,
        description="Port for HTTP transport",
    )

    @field_validator("ozon_api_base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Reject base URL changes — SSRF protection."""
        allowed = "https://api-seller.ozon.ru"
        if v != allowed:
            msg = f"ozon_api_base_url must be {allowed!r} (SSRF protection)"
            raise ValueError(msg)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            msg = f"log_level must be one of {allowed}"
            raise ValueError(msg)
        return upper


def get_settings() -> Settings:
    """Settings factory (can be overridden in tests)."""
    return Settings()  # type: ignore[call-arg]
