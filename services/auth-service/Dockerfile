FROM python:3.13-slim

# Install UV from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy the application into the container
COPY . /app

# Install dependencies
WORKDIR /app
RUN uv sync --frozen --no-cache

# Set permissions
RUN chown -R appuser:appgroup /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8001", "--host", "0.0.0.0"]
