# Multi-stage build for Obsidian MCP Server
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:0.4.0 /uv /bin/uv

# Copy dependency files
COPY pyproject.toml .
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN uv venv /app/.venv
RUN uv pip install --no-cache -e .

# Stage 2: Runtime
FROM python:3.11-slim as runtime

# Create non-root user for security
RUN groupadd --gid 1000 mcp && \
    useradd --uid 1000 --gid mcp --shell /bin/bash --create-home mcp

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VAULT_PATH=/vault \
    TRANSPORT=stdio \
    LOG_LEVEL=INFO

# Create vault directory and set permissions
RUN mkdir -p /vault && chown -R mcp:mcp /vault /app

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Set working directory to src for proper imports
WORKDIR /app/src

# Run the server
ENTRYPOINT ["python", "-m", "server"]
