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

# TODO (Milestone 23): Implement create_app() factory with CORS, routers, lifespan
# TODO (Milestone 23): Add /api/v1/monitoring/health endpoint
# TODO (Milestone 29): Mount WebSocket router


def main() -> None:
    """Launch Uvicorn ASGI server. Implemented in Milestone 23."""
    raise NotImplementedError(
        "mitigation_engine.main is scaffolded. Implement in Milestone 23."
    )


if __name__ == "__main__":
    main()
