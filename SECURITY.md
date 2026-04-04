# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email: [security contact — create a GitHub Security Advisory instead]
3. Use [GitHub Security Advisories](https://github.com/YOUR_USERNAME/ozon-mcp-server/security/advisories/new)

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
