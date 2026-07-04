"""mitigation_engine/main.py"""

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
