# Multi-stage Dockerfile: build in a builder stage then copy only runtime artifacts
FROM python:3.13.6-slim AS builder
ENV UV_INSTALL_DIR=/usr/local/bin
ENV PATH=/usr/local/bin:$PATH
ARG UV_VERSION=0.8.12

WORKDIR /build
COPY pyproject.toml uv.lock ./

# Install build deps, install uv system-wide and run uv sync in a temporary build dir.
# Remove any created virtualenv to avoid copying it into the final /app layer.
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl ca-certificates libpq-dev \
  && curl -fsSL https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh -s -- $UV_VERSION \
  && uv sync --frozen --no-cache \
  && rm -rf /var/lib/apt/lists/* /build/.venv

WORKDIR /app
COPY . /app
RUN rm -rf /app/.venv
RUN chown -R 1000:1000 /app /usr/local

# Final runtime image: copy venv and app
FROM python:3.13.6-slim AS runtime
ENV PATH=/usr/local/bin:$PATH
ENV HOME=/home/appuser
ENV XDG_CACHE_HOME=/home/appuser/.cache

# Create non-root user and home
RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/appuser -s /sbin/nologin appuser \
  && mkdir -p /home/appuser/.cache \
  && chown -R appuser:appgroup /home/appuser

# Copy installed system files and app from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Minimal runtime OS deps
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates libpq5 \
  && rm -rf /var/lib/apt/lists/* \
  && chown -R appuser:appgroup /app

USER appuser
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
