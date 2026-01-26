from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.session import get_db
from schemas.job import Job, JobStatus
from services.job_service import (
    get_jobs,
    get_job,
    cancel_job,
    get_job_status
)
from api.deps import get_current_active_user
from schemas.user import User

router = APIRouter()


@router.get("/", response_model=List[Job])
def list_jobs(
    skip: int = 0, 
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all jobs for the current user
    """
    jobs = get_jobs(db, owner_id=current_user.id, skip=skip, limit=limit)
    
    # Filter by status if specified
    if status is not None:
        jobs = [j for j in jobs if j.status == status]
    
    return jobs


@router.get("/{job_id}", response_model=Job)
def get_job_by_id(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get job by ID
    """
    job = get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return job


@router.get("/{job_id}/status", response_model=JobStatus)
def check_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Check the status of a job
    """
    job = get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job status not found")
    return JobStatus(**status)


@router.post("/{job_id}/cancel")
def cancel_job_by_id(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Cancel a running job
    """
    job = get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if job.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    success = cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel job")
    
    # Update job status in database
    from services.job_service import update_job
    update_job(db, job_id, {"status": "cancelled"})
    
    return {"status": "cancelled"}


@router.get("/{job_id}/logs")
def get_job_logs(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get job logs
    """
    job = get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return {"job_id": job_id, "logs": job.logs or ""}
