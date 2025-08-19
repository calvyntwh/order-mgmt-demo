FROM python:3.13.6-slim

# Upgrade OS packages and install curl + ca-certificates, then install uv via official installer
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y --no-install-recommends \
  && apt-get install -y --no-install-recommends curl ca-certificates libpq5 \
  && rm -rf /var/lib/apt/lists/*

ENV UV_INSTALL_DIR=/usr/local/bin
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN UV_NO_MODIFY_PATH=1 sh /uv-installer.sh && rm -f /uv-installer.sh

# Non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Ensure a writable home and cache directory for the non-root user so `uv` can
# create its cache under $HOME/.cache without permission errors.
RUN mkdir -p /home/appuser/.cache \
  && chown -R appuser:appgroup /home/appuser
ENV HOME=/home/appuser
ENV XDG_CACHE_HOME=/home/appuser/.cache

# Copy the application into the container

# Use app directory and copy dependency manifests first for better layer caching
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Install dependencies from lockfile
RUN uv sync --frozen --no-cache

# Now copy the rest of the application
COPY . /app

# Set permissions
RUN chown -R appuser:appgroup /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Run the app via system python + uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
