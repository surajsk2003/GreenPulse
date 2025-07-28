from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import buildings, energy, analytics, insights, ml_analytics
from .websocket import websocket_endpoint

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("🚀 GreenPulse API started successfully!")
    yield
    # Shutdown
    print("🛑 GreenPulse API shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart Energy Management Platform for Campuses",
    version=settings.VERSION,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(buildings.router, prefix=f"{settings.API_V1_STR}/buildings", tags=["buildings"])
app.include_router(energy.router, prefix=f"{settings.API_V1_STR}/energy", tags=["energy"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(insights.router, prefix=f"{settings.API_V1_STR}/insights", tags=["insights"])
app.include_router(ml_analytics.router, tags=["ml-analytics"])

# WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)

@app.get("/")
async def root():
    return {
        "message": "🌱 GreenPulse API - Smart Energy Management",
        "version": settings.VERSION,
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "greenpulse-api",
        "version": settings.VERSION
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )