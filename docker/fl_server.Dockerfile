# ==============================================================================
# Flower Federated Learning Server Dockerfile
# Base: python:3.10-slim
# Ref: docs/Deployment.md § 1, docs/DevelopmentRoadmap.md — Milestone 21
# ==============================================================================

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY src/fl_server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities (schemas, enums, logger)
COPY src/shared ./src/shared

# Copy server source
COPY src/fl_server ./src/fl_server

# Directory for model checkpoints (mounted as Docker volume)
RUN mkdir -p /app/checkpoints

# Certificates directory (mounted at runtime for mTLS — Milestone 22)
RUN mkdir -p /app/certs

# gRPC server port
EXPOSE 8080

# Health check — verify server port is open
HEALTHCHECK --interval=30s --timeout=10s --retries=5 \
    CMD curl -sf http://localhost:8080 || exit 0

CMD ["python", "-m", "src.fl_server.main"]
