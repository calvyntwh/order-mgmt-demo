FROM python:3.13.6-slim

# Install UV from official image (pinned tag for reproducible builds)
# NOTE: for maximum reproducibility replace the tag with a digest (sha256:...)
# Patch OS packages (reduce known CVEs like zlib) and install curl for health checks
# This upgrades packages from the base image to the latest available in the distro
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y --no-install-recommends \
  && apt-get install -y --no-install-recommends curl ca-certificates libpq5 \
  && rm -rf /var/lib/apt/lists/*

# Install uv via the official installer (use curl to avoid storing a fetched file in the image)
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -fsSL https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh -s --

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
  CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

# Run the app via system python + uvicorn (works regardless of venv path)
# Use module form so the installed uvicorn entrypoint is invoked from site-packages
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
