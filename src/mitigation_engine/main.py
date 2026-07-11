"""mitigation_engine/main.py"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mitigation_engine.config import settings
from mitigation_engine.api import alerts, auth, metrics, websocket
from mitigation_engine.db.database import close_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await close_engine()

app = FastAPI(
    title="DDoS Mitigation Engine API",
    description="Adaptive FL DDoS System - Centralized API Gateway",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(metrics.router)
app.include_router(websocket.router)

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
