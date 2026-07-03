# ==============================================================================
# Ryu SDN Controller Dockerfile
# Base: python:3.10-slim (Ryu is a Python framework)
# Ref: docs/Deployment.md § 1, docs/DevelopmentRoadmap.md — Milestone 39
#
# NOTE: Ryu runs as a separate process from Mininet.
#       Mininet requires a Linux environment with kernel support for OvS.
#       Use docker-compose.mininet.yml for the full SDN simulation stack.
# ==============================================================================

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (Ryu requires some build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Ryu and related dependencies
RUN pip install --no-cache-dir \
    ryu==4.34 \
    eventlet==0.33.3 \
    oslo.config==9.3.0 \
    loguru==0.7.2 \
    httpx==0.26.0

# Copy SDN controller application
COPY src/sdn_controller ./sdn_controller
COPY src/shared ./shared

# Ryu REST API port (for mitigation commands from Mitigation Engine)
EXPOSE 8080

# Ryu OpenFlow port
EXPOSE 6633
EXPOSE 6653

# Start the Ryu controller with our custom app
CMD ["ryu-manager", "--verbose", "sdn_controller/ryu_app.py", "sdn_controller/mitigation_api.py"]
