FROM python:3.14-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir build \
    && python -m build --wheel --outdir /dist

FROM python:3.14-slim

# Безопасность: non-root пользователь
RUN groupadd -r mcp && useradd -r -g mcp -d /app -s /sbin/nologin mcp

WORKDIR /app

COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

# Переключаемся на non-root
USER mcp

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "-m", "ozon_mcp_server"]
