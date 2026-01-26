"""
TerraSim API - FastAPI Application

This module initializes the FastAPI application and includes all API routes.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from api.v1.api import api_router
from api.deps import get_current_user
from schemas.user import User

# Initialize FastAPI app
app = FastAPI(
    title="TerraSim API",
    description="Open-Source GIS Erosion Modeling Platform",
    version="3.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint that provides API information."""
    return {
        "name": "TerraSim API",
        "version": "3.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_v1": "/api/v1"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy"}

# Example protected route
@app.get("/api/v1/secure")
async def secure_endpoint(current_user: dict = Depends(get_current_user)):
    """Example of a protected endpoint."""
    return {"message": "This is a secure endpoint", "user": current_user}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Run with: uvicorn backend.api:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
