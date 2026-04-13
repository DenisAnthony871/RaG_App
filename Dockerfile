FROM python:3.12-slim@sha256:804ddf3251a60bbf9c92e73b7566c40428d54d0e79d3428194edf40da6521286

WORKDIR /app

# Install system dependencies and upgrade packages to patch known CVEs
# (CVE-2026-28389, CVE-2026-28390, CVE-2026-28391 — openssl < 3.5.5-1~deb13u2)
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

# Expose API port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
