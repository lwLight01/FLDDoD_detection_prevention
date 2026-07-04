# ==============================================================================
# Flower FL Client Dockerfile
# Base: python:3.10-slim
# Ref: docs/Deployment.md § 1, docs/DevelopmentRoadmap.md — Milestone 21
# ==============================================================================

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY src/fl_client/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities (Pydantic schemas, enums, logger)
COPY src/shared ./src/shared

# Copy client source
COPY src/fl_client ./src/fl_client

# Directory for local data partition (mounted at runtime)
RUN mkdir -p /app/data/local_partition

# Certificates directory (mounted at runtime for mTLS — Milestone 22)
RUN mkdir -p /app/certs

# gRPC client does not bind a port; expose for metrics/healthcheck
EXPOSE 8081

# CLIENT_ID, DATA_PATH, SERVER_ADDRESS overridden at runtime via env vars
ENV CLIENT_ID=client_0
ENV DATA_PATH=/app/data/local_partition/partition.csv
ENV SCALER_PATH=/app/data/quantile_scaler.pkl
ENV SERVER_ADDRESS=fl_server:8080

CMD ["sh", "-c", "python -m src.fl_client.main \
    --client-id ${CLIENT_ID} \
    --data-path ${DATA_PATH} \
    --scaler-path ${SCALER_PATH} \
    --server-address ${SERVER_ADDRESS}"]
