"""
TerraSim API v1 Router

This module contains all API v1 endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List

from ....core.config import settings
from .endpoints import (
    auth,
    users,
    projects,
    pointclouds,
    rasters,
    analysis,
    models,
    jobs
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(pointclouds.router, prefix="/pointclouds", tags=["pointclouds"])
api_router.include_router(rasters.router, prefix="/rasters", tags=["rasters"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

@api_router.get("/health")
async def health_check() -> dict:
    """Health check endpoint for API v1"""
    return {"status": "ok", "version": "v1"}
