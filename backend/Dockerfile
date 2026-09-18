# ==============================================================================
# PÁRAMO URBANO (v2.0.0 Core) — Backend Dockerfile (Multi-Stage Production Build)
# "Donde el asfalto toca la cumbre"
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Dependency Wheel Compilation
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install minimal compilation utilities for C-extensions (asyncpg, greenlet, argon2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create isolated Python virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Production Distroless/Minimal Runner
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install runtime shared libraries (libpq for postgresql asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group
RUN groupadd -g 10001 nonroot && \
    useradd -u 10001 -g nonroot -s /bin/bash -m nonroot

WORKDIR /app

# Copy isolated virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy backend application source code, data knowledge bases, and schema configurations
COPY --chown=nonroot:nonroot backend /app/backend
COPY --chown=nonroot:nonroot data /app/data
COPY --chown=nonroot:nonroot .env.example /app/.env.example

# Set directory permissions for unprivileged user
RUN chown -R nonroot:nonroot /app

USER nonroot:nonroot

EXPOSE 8000

# Native healthcheck using standard library urllib without external dependencies
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default entrypoint starts FastAPI Core REST API Gateway
CMD ["uvicorn", "backend.src.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
