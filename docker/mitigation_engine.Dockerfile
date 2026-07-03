# ==============================================================================
# Mitigation Engine Dockerfile
# Base: python:3.10-slim
# Ref: docs/Deployment.md § 1, docs/DevelopmentRoadmap.md — Milestone 23
# ==============================================================================

FROM python:3.10-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY src/mitigation_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module (required by mitigation_engine imports)
COPY src/shared ./shared

# Copy application source
COPY src/mitigation_engine ./mitigation_engine

# Expose FastAPI port
EXPOSE 8000

# Health-check curl command (matches Docker Compose healthcheck)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/monitoring/health || exit 1

# Run with Uvicorn — reload disabled in production
CMD ["uvicorn", "mitigation_engine.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
