# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies required by psycopg, asyncpg, tiktoken, and embedded redis
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    curl \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source
COPY . .

# Ensure start script is executable
RUN chmod +x start.sh

# ── Web service entrypoint ────────────────────────────────────────────────────
CMD ["./start.sh"]