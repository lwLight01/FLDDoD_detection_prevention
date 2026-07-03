# ==============================================================================
# Flower FL Client Dockerfile
# Base: python:3.10-slim
# Ref: docs/Deployment.md § 1, docs/DevelopmentRoadmap.md — Milestone 21
# ==============================================================================

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY src/fl_client/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities (Pydantic schemas, enums, logger)
COPY src/shared ./shared

# Copy client source
COPY src/fl_client ./fl_client

# Directory for local data partition (mounted at runtime)
RUN mkdir -p /app/data/local_partition

# gRPC client does not expose a server port, but expose for metrics/healthcheck
EXPOSE 8081

CMD ["python", "-m", "fl_client.main"]
