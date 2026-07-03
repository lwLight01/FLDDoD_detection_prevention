# ==============================================================================
# Flower Federated Learning Server Dockerfile
# Base: python:3.10-slim
# Ref: docs/Deployment.md § 1, docs/DevelopmentRoadmap.md — Milestone 21
# ==============================================================================

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY src/fl_server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/shared ./shared
COPY src/fl_server ./fl_server

# Directory for model checkpoints (mounted as Docker volume)
RUN mkdir -p /app/checkpoints

EXPOSE 8080

CMD ["python", "-m", "fl_server.main"]
