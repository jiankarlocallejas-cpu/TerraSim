import os
import json
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.job import Job
from schemas.job import JobCreate, JobUpdate

logger = logging.getLogger(__name__)


def get_job(db: Session, job_id: str) -> Optional[Job]:
    """Get a job by ID"""
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Job]:
    """Get a list of jobs for a specific owner"""
    return (
        db.query(Job)
        .filter(Job.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_job(db: Session, job: JobCreate, owner_id: int) -> Job:
    """Create a new job"""
    job_id = str(uuid.uuid4())
    db_job = Job(
        id=job_id,
        name=job.name,
        description=job.description,
        job_type=job.job_type,
        parameters=job.parameters,
        analysis_id=job.analysis_id,
        owner_id=owner_id,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job(db: Session, job_id: str, job: JobUpdate) -> Optional[Job]:
    """Update a job"""
    db_job = get_job(db, job_id=job_id)
    if not db_job:
        return None
    
    update_data = job.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, job_id: str) -> bool:
    """Delete a job"""
    db_job = get_job(db, job_id=job_id)
    if not db_job:
        return False
    
    db.delete(db_job)
    db.commit()
    return True


def start_job(db: Session, job_id: str) -> bool:
    """Start a job"""
    db_job = get_job(db, job_id=job_id)
    if not db_job:
        return False
    
    update_data = JobUpdate(
        status="running",
        started_at=datetime.utcnow(),
        progress=0
    )
    update_job(db, job_id, update_data)
    return True


def complete_job(db: Session, job_id: str, result: Dict[str, Any]) -> bool:
    """Complete a job"""
    db_job = get_job(db, job_id=job_id)
    if not db_job:
        return False
    
    update_data = JobUpdate(
        status="completed",
        completed_at=datetime.utcnow(),
        progress=100,
        result=result
    )
    update_job(db, job_id, update_data)
    return True


def fail_job(db: Session, job_id: str, error_message: str) -> bool:
    """Mark a job as failed"""
    db_job = get_job(db, job_id=job_id)
    if not db_job:
        return False
    
    update_data = JobUpdate(
        status="failed",
        completed_at=datetime.utcnow(),
        logs=error_message
    )
    update_job(db, job_id, update_data)
    return True


def cancel_job(job_id: str) -> bool:
    """Cancel a running job"""
    # This is a placeholder for job cancellation
    # In a real implementation, this would:
    # 1. Check if the job is running
    # 2. Send a cancellation signal to the worker
    # 3. Update the job status
    
    logger.info(f"Cancelling job {job_id}")
    return True


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the current status of a job"""
    # This is a placeholder for job status checking
    # In a real implementation, this would:
    # 1. Check the job status in the database
    # 2. Check with the worker if the job is running
    # 3. Return current progress and status
    
    return {
        "job_id": job_id,
        "status": "running",
        "progress": 50,
        "message": "Processing..."
    }


def update_job_progress(db: Session, job_id: str, progress: int, message: str = None) -> bool:
    """Update job progress"""
    db_job = get_job(db, job_id=job_id)
    if not db_job:
        return False
    
    update_data = JobUpdate(
        progress=progress,
        logs=message if message else db_job.logs
    )
    update_job(db, job_id, update_data)
    return True


def append_job_log(db: Session, job_id: str, log_message: str) -> bool:
    """Append a log message to a job"""
    db_job = get_job(db, job_id=job_id)
    if not db_job:
        return False
    
    current_logs = db_job.logs or ""
    timestamp = datetime.utcnow().isoformat()
    new_log = f"[{timestamp}] {log_message}\n"
    updated_logs = current_logs + new_log
    
    update_data = JobUpdate(logs=updated_logs)
    update_job(db, job_id, update_data)
    return True
