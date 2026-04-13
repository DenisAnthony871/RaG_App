FROM python:3.12-slim@sha256:804ddf3251a60bbf9c92e73b7566c40428d54d0e79d3428194edf40da6521286

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

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
