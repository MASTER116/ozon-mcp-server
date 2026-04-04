# Contributing

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/ozon-mcp-server.git
cd ozon-mcp-server

# Install dependencies (using uv)
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install

# Copy env template
cp .env.example .env
# Edit .env with your Ozon API credentials

# Start infrastructure
docker compose up -d postgres redis

# Run tests
uv run pytest -v

# Run linter
uv run ruff check src/ tests/

# Run type checker
uv run mypy src/

# Run security scan
uv run bandit -r src/ -c pyproject.toml
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Ensure all checks pass: `uv run pytest && uv run ruff check . && uv run mypy src/`
5. Commit with conventional commits (`feat:`, `fix:`, `docs:`, `security:`)
6. Open a Pull Request

## Code Standards

- **Python 3.12+** with type annotations
- **Pydantic v2** for all input validation
- **ruff** for linting and formatting
- **mypy strict** for type checking
- **80%+ test coverage** required
- All secrets via `SecretStr` — never hardcode

## Security

If you find a security vulnerability, **DO NOT** open a public issue.
See [SECURITY.md](SECURITY.md) for reporting instructions.
