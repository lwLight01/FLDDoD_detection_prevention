"""
mitigation_engine/main.py
--------------------------
FastAPI application factory and entry point.

Mounts:
  - /api/v1/auth        — JWT authentication (Milestone 23)
  - /api/v1/inference   — Alert ingestion from edge clients (Milestone 24)
  - /api/v1/mitigation  — Mitigation management (Milestone 27)
  - /api/v1/federated   — FL state queries (Milestone 20)
  - /api/v1/dashboard   — Analytics endpoints (Milestone 34)
  - /api/v1/logs        — System logs (Milestone 34)
  - /api/v1/admin       — Admin controls (Milestone 37)
  - /api/v1/monitoring  — Health check (Milestone 23)
  - /ws/v1/dashboard    — WebSocket live feed (Milestone 29)

Implementation deferred to Milestone 23.

Ref: docs/API.md, docs/Deployment.md
     docs/DevelopmentRoadmap.md — Milestone 23
"""

from fastapi import FastAPI
from pydantic import BaseModel

# TODO (Milestone 23): Add CORS, routers, and lifespan

app = FastAPI(
    title="DDoS Mitigation Engine API",
    description="Adaptive FL DDoS System - Centralized API Gateway",
    version="1.0.0",
)


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/api/v1/monitoring/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Health check endpoint for Docker Compose."""
    return HealthResponse(status="ok", message="Mitigation Engine API is running.")


def main() -> None:
    import uvicorn

    uvicorn.run("mitigation_engine.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
