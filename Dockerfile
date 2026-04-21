ARG PLATFORM=linux/amd64
<<<<<<< HEAD
# We intentionally use the unpinned tag (python:3.12-slim) instead of a sha256 digest.
# This enables deterministic multi-arch builds using the --platform arg.
# We rely on `apt-get upgrade` below and periodic CI rebuilds for security.
=======
>>>>>>> b40c08e4ffd3a63e1801b68deb8333adb42f56cf
FROM --platform=${PLATFORM} python:3.12-slim AS base

WORKDIR /app

# Install system dependencies and apply all available security patches
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency installation (pinned for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

# Copy dependency file first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN uv pip install -r requirements.txt --system

# Copy application source
COPY *.py .
COPY .env.example .

# Create a non-root user for runtime security
RUN groupadd --system appuser \
    && useradd --system --gid appuser --no-create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser

# Expose API port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
