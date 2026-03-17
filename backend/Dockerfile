# Multi-stage build: slim final image
FROM python:3.11-slim as builder

WORKDIR /tmp/build

# Install build dependencies with retry logic
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends --fix-missing \
    -o APT::Acquire::Retries=3 \
    -o APT::Install::Recommends=false \
    build-essential \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir setuptools wheel packaging

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user --no-build-isolation -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends --fix-missing \
    -o APT::Acquire::Retries=3 \
    -o APT::Install::Recommends=false \
    ffmpeg \
    libportaudio2 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set PATH to use local Python packages
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Make entrypoint executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 5001), timeout=5)" || exit 1

EXPOSE 5001

ENTRYPOINT ["/app/entrypoint.sh"]
