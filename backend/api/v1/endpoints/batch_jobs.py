"""
Batch Job Processing API Endpoints
Endpoints for submitting and managing multiple concurrent jobs
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.session import get_db
from api.deps import get_current_active_user
from schemas.user import User
from services.worker_pool import (
    get_worker_pool,
    get_batch_manager,
    submit_parallel_simulations
)
from pydantic import BaseModel

router = APIRouter()


class JobSubmission(BaseModel):
    """Single job submission"""
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 0


class BatchSubmission(BaseModel):
    """Batch of jobs submission"""
    jobs: List[JobSubmission]
    batch_name: Optional[str] = None


class WorkerStats(BaseModel):
    """Worker pool statistics"""
    max_workers: int
    active_workers: int
    queued_jobs: int
    total_jobs: int
    worker_type: str


class BatchStatus(BaseModel):
    """Batch execution status"""
    batch_id: str
    total_jobs: int
    completed: int
    failed: int
    running: int
    queued: int
    progress_percent: int
    job_statuses: List[Dict[str, Any]]


# ============================================================================
# WORKER POOL MANAGEMENT
# ============================================================================

@router.get("/pool/stats", response_model=WorkerStats)
def get_pool_statistics():
    """Get current worker pool statistics"""
    pool = get_worker_pool()
    stats = pool.get_worker_stats()
    return WorkerStats(**stats)


@router.get("/pool/jobs")
def list_active_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all active jobs in the worker pool"""
    pool = get_worker_pool()
    jobs = pool.get_active_jobs()
    
    return {
        "total_jobs": len(jobs),
        "jobs": jobs
    }


# ============================================================================
# BATCH JOB SUBMISSION
# ============================================================================

@router.post("/batch/submit", response_model=Dict[str, Any])
def submit_batch_jobs(
    batch: BatchSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit a batch of jobs for parallel execution
    
    Example:
    {
        "batch_name": "erosion_scenario_analysis",
        "jobs": [
            {
                "task_type": "erosion_simulation",
                "parameters": {"rainfall": 100, "cover_factor": 0.5},
                "priority": 0
            },
            {
                "task_type": "erosion_simulation",
                "parameters": {"rainfall": 150, "cover_factor": 0.5},
                "priority": 1
            },
            {
                "task_type": "erosion_simulation",
                "parameters": {"rainfall": 200, "cover_factor": 0.5},
                "priority": 2
            }
        ]
    }
    """
    batch_manager = get_batch_manager()
    
    # Convert job submissions to job configs
    job_configs = []
    for job in batch.jobs:
        # Map task_type to actual function
        task_func = _get_task_function(job.task_type)
        if not task_func:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task type: {job.task_type}"
            )
        
        job_config = {
            "task_func": task_func,
            "kwargs": job.parameters,
            "priority": job.priority
        }
        job_configs.append(job_config)
    
    # Submit batch
    result = batch_manager.submit_batch(
        batch_id=f"batch_{current_user.id}_{len(batch.jobs)}_jobs",
        jobs=job_configs
    )
    
    return result


@router.get("/batch/{batch_id}/status", response_model=BatchStatus)
def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get status of a batch"""
    batch_manager = get_batch_manager()
    
    status = batch_manager.get_batch_status(batch_id)
    if not status:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return BatchStatus(**status)


# ============================================================================
# PARALLEL SIMULATIONS
# ============================================================================

@router.post("/simulations/parallel")
def submit_parallel_simulations_endpoint(
    dem_id: int,
    scenario_parameters: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit multiple erosion simulations with different parameters to run in parallel
    
    Example:
    {
        "dem_id": 1,
        "scenario_parameters": [
            {"rainfall": 100, "cover_factor": 0.5, "management": "baseline"},
            {"rainfall": 100, "cover_factor": 0.7, "management": "reforestation"},
            {"rainfall": 100, "cover_factor": 0.3, "management": "aggressive_grazing"}
        ]
    }
    """
    from services.raster_service import _raster_service
    import numpy as np
    
    # Load DEM
    raster = _raster_service.get_by_id(db, dem_id)
    if not raster:
        raise HTTPException(status_code=404, detail="DEM not found")
    
    # Load DEM data from file
    try:
        import rasterio
        with rasterio.open(raster.file_path) as src:
            dem_data = src.read(1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load DEM: {str(e)}")
    
    # Submit parallel simulations
    batch_id = submit_parallel_simulations(
        db=db,
        dem_data=dem_data,
        parameters_list=scenario_parameters
    )
    
    return {
        "batch_id": batch_id,
        "dem_id": dem_id,
        "num_scenarios": len(scenario_parameters),
        "status": "submitted",
        "message": "Parallel simulations submitted to worker pool"
    }


# ============================================================================
# JOB MANAGEMENT
# ============================================================================

@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a queued job"""
    pool = get_worker_pool()
    
    success = pool.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Job cannot be cancelled (either not found or already running)"
        )
    
    return {"status": "cancelled", "job_id": job_id}


@router.get("/jobs/{job_id}/status")
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get status of a specific job"""
    pool = get_worker_pool()
    
    status = pool.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        **status
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_task_function(task_type: str):
    """Map task type to actual function"""
    from backend.services.simulation_engine import get_simulation_engine
    
    task_mapping = {
        "erosion_simulation": get_simulation_engine().run_single_simulation,
        "pointcloud_processing": None,  # Add actual function
        "raster_analysis": None,  # Add actual function
    }
    
    return task_mapping.get(task_type)
