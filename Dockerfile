# Multi-stage Dockerfile for Heckx AI Video Generator
# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/venv/bin:$PATH"
ENV ENVIRONMENT=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    libsndfile1 \
    espeak \
    espeak-data \
    libespeak1 \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set work directory
WORKDIR /app

# Create non-root user first
RUN groupadd -r heckx && useradd -r -g heckx -d /app -s /bin/bash heckx

# Create necessary directories
RUN mkdir -p /app/temp \
    /app/logs \
    /app/data \
    /app/uploads \
    /app/downloads \
    /app/previews \
    /app/config \
    /app/scripts

# Copy application code
COPY --chown=heckx:heckx . .

# Set permissions
RUN chmod +x scripts/*.sh 2>/dev/null || true
RUN chown -R heckx:heckx /app

# Switch to non-root user
USER heckx

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:5001/api/health || exit 1

# Expose ports
EXPOSE 5001 5002

# Default command with production settings
CMD ["python", "-m", "video_generator.main_service"]

# Development stage
FROM production as development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    nano \
    htop \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    flake8 \
    isort \
    mypy

USER heckx

# Override command for development
CMD ["python", "-m", "video_generator.web_interface"]