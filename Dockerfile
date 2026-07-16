# ─────────────────────────────────────────────────────────────
# Nexus AI Assistant — Dockerfile
# Multi-stage build for lean production image
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Nexus AI Assistant"
LABEL org.opencontainers.image.description="Self-hosted Telegram AI companion"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# System runtime deps (for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create data and logs directories
RUN mkdir -p data logs

# Ensure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('data/nexus.db').close(); print('OK')" || exit 1

# Non-root user
RUN useradd -m -u 1000 nexus && chown -R nexus:nexus /app
USER nexus

CMD ["python", "main.py"]
