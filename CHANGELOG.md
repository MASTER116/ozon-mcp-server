# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-04

### Added

- **13 MCP tools** for Ozon Seller API:
  - Products: `get_product_list`, `get_product_info`, `get_stock_on_warehouses`, `create_product`, `update_prices`, `update_stocks`, `archive_product`
  - Orders: `get_fbs_orders`, `get_fbo_orders`
  - Analytics: `get_analytics`, `get_finance_report`
  - Warehouses: `get_warehouse_list`
- **6-layer security architecture** (OWASP MCP Top 10 compliance):
  - Bearer token authentication with constant-time comparison
  - SSRF prevention (hardcoded base URL, private IP blocking, redirect prohibition)
  - Strict Pydantic v2 input validation with allowlists
  - Redis-backed Token Bucket rate limiting (global + per-write)
  - Credential masking via `SecretStr` and regex output sanitization
  - PostgreSQL audit logging with secret masking
- **Circuit breaker** for Ozon API resilience (auto-cutoff after consecutive failures)
- **Redis caching** with category-based invalidation and configurable TTL
- **MCP resource** `audit://recent` for audit log access
- **Docker Compose** deployment (MCP server + Redis + PostgreSQL)
- **CI/CD pipeline** via GitHub Actions (lint, typecheck, security scan, test, Docker build)
- **Pre-commit hooks** (ruff, mypy, bandit)
- Professional English documentation (README, SECURITY.md, CONTRIBUTING.md)
