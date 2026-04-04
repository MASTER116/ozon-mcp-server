# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email: [security contact — create a GitHub Security Advisory instead]
3. Use [GitHub Security Advisories](https://github.com/MASTER116/ozon-mcp-server/security/advisories/new)

We will respond within 48 hours.

## Threat Model

This MCP server handles **real e-commerce operations** (pricing, inventory, orders). A security breach could result in financial loss for sellers.

### Assets Protected

| Asset | Sensitivity | Protection |
|-------|-----------|------------|
| Ozon API Key | **Critical** | SecretStr, env vars, never logged |
| Seller financial data | High | Audit logging, access control |
| Product pricing | High | Write rate limiting, destructiveHint annotations |
| Customer order data | High | No PII stored locally, pass-through only |

### Attack Surface

| Vector | Risk | Mitigation |
|--------|------|------------|
| SSRF via endpoint manipulation | Critical | Hardcoded base URL, private IP blocking, no redirects |
| Prompt injection via tool params | High | Pydantic strict validation, allowlists, no dynamic queries |
| Credential leaking in responses | High | SecretStr, output sanitization, regex filtering |
| Rate limit bypass | Medium | Redis Token Bucket, per-tool limits, circuit breaker |
| MCP client impersonation | Medium | Bearer auth, constant-time comparison |
| Supply chain attack | Medium | Dependabot, pip-audit, bandit, pinned dependencies |
| Denial of Service | Medium | Input size limits, max_length on all fields |

### OWASP MCP Top 10 Coverage

| Risk | Status | Implementation |
|------|--------|---------------|
| MCP01: Token Mismanagement | ✅ Mitigated | SecretStr, env vars, auto-rotation support |
| MCP02: Privilege Escalation | ✅ Mitigated | Tool annotations, read/write separation |
| MCP03: Tool Poisoning | ✅ Mitigated | Static tool definitions, no dynamic descriptions |
| MCP04: Supply Chain | ✅ Mitigated | Dependabot, pip-audit, bandit CI |
| MCP05: Command Injection | ✅ Mitigated | No shell calls, Pydantic validation |
| MCP06: Intent Flow Subversion | ✅ Mitigated | Strict types, allowlist enums |
| MCP07: Insufficient Auth | ✅ Mitigated | Bearer auth middleware |
| MCP08: Lack of Audit | ✅ Mitigated | PostgreSQL audit log |
| MCP09: Shadow MCP Servers | ⚠️ Partial | Docker-only deployment recommended |
| MCP10: Context Over-Sharing | ✅ Mitigated | Output sanitization, credential filtering |

## Production Hardening Checklist

Before deploying to production, verify each item:

### Secrets
- [ ] `OZON_API_KEY` — unique per environment, rotated every 180 days
- [ ] `POSTGRES_PASSWORD` — generated via `openssl rand -base64 32`, not reused
- [ ] `REDIS_PASSWORD` — generated via `openssl rand -base64 32`, not reused
- [ ] `MCP_AUTH_TOKEN` — set for `streamable-http` transport (required if exposed to network)
- [ ] `.env` file has `chmod 600` permissions (owner-only read/write)
- [ ] `.env` is in `.gitignore` and never committed

### Docker
- [ ] Use `docker-compose.prod.yml` (not the dev compose file)
- [ ] All containers have `cap_drop: ALL` + only required capabilities added back
- [ ] `no-new-privileges: true` on all containers
- [ ] `read_only: true` on application containers
- [ ] MCP port bound to `127.0.0.1` (use reverse proxy like nginx/caddy for external access)
- [ ] PostgreSQL and Redis are NOT exposed to host (internal network only)
- [ ] Resource limits (memory + CPU) are set on all containers

### Redis
- [ ] `requirepass` is set with a strong password
- [ ] Dangerous commands disabled: `FLUSHDB`, `FLUSHALL`, `CONFIG`, `KEYS`, `DEBUG`
- [ ] AOF persistence enabled for rate limit state durability

### PostgreSQL
- [ ] `scram-sha-256` authentication (set via `POSTGRES_INITDB_ARGS`)
- [ ] Init script creates audit table with indexes on first start
- [ ] Regular backups configured (use `pg-backup` maintenance profile)
- [ ] Audit cleanup configured (90-day retention via `audit-cleanup` profile)

### Network
- [ ] Reverse proxy (nginx/caddy) with TLS for external `streamable-http` access
- [ ] Firewall: only ports 80/443 (reverse proxy) open to the internet
- [ ] Docker internal network isolates DB and Redis from external access

### Monitoring
- [ ] Container health checks are active (`docker compose ps`)
- [ ] Log rotation is configured (json-file driver with max-size)
- [ ] Alert on circuit breaker open events (search for `circuit_breaker_opened` in logs)
- [ ] Alert on rate limit exceeded events (search for `rate_limit_exceeded` in logs)

## Security Testing

Run security checks locally:

```bash
# Static analysis
uv run bandit -r src/ -c pyproject.toml

# Dependency audit
uv run pip-audit

# Security test suite
uv run pytest tests/security/ -v
```

## Dependencies

All dependencies are pinned and audited:

- **fastmcp**: MCP framework (MIT)
- **httpx**: HTTP client (BSD)
- **pydantic**: Validation (MIT)
- **asyncpg**: PostgreSQL driver (Apache 2.0)
- **redis**: Redis client (MIT)
- **structlog**: Logging (MIT/Apache 2.0)
- **tenacity**: Retry logic (Apache 2.0)
