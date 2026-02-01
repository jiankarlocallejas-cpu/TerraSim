from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.session import get_db
from schemas.pointcloud import PointCloud, PointCloudCreate, PointCloudProcess, PointCloudStats
from services.geospatial import (
    process_pointcloud_file,
    get_pointclouds,
    get_pointcloud,
    delete_pointcloud,
    get_pointcloud_stats,
    create_pointcloud
)
from api.deps import get_current_active_user
from core.config import settings
from schemas.user import User

router = APIRouter()


@router.post("/upload/", response_model=PointCloud)
async def upload_pointcloud(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload a point cloud file (LAS/LAZ)
    """
    if not file.filename.endswith(('.las', '.laz')):
        raise HTTPException(status_code=400, detail="File must be .las or .laz format")
    
    # Save file temporarily
    upload_dir = f"{settings.LOCAL_STORAGE_PATH}/uploads/pointclouds"
    os.makedirs(upload_dir, exist_ok=True)
    file_location = f"{upload_dir}/{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    
    # Create point cloud record
    pointcloud_data = PointCloudCreate(
        name=file.filename,
        file_path=file_location
    )
    
    # Process in background
    background_tasks.add_task(
        process_pointcloud_file,
        file_path=file_location,
        user_id=current_user.id,
        db=db
    )
    
    from services.geospatial import create_pointcloud
    db_pointcloud = create_pointcloud(db, pointcloud_data, current_user.id)
    
    return db_pointcloud


@router.get("/", response_model=List[PointCloud])
def list_pointclouds(
    skip: int = 0, 
    limit: int = 100,
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all point clouds for the current user
    """
    pointclouds = get_pointclouds(db, owner_id=current_user.id, skip=skip, limit=limit)
    
    # Filter by project if specified
    if project_id is not None:
        pointclouds = [pc for pc in pointclouds if pc.project_id == project_id]
    
    return pointclouds


@router.get("/{pointcloud_id}", response_model=PointCloud)
def get_pointcloud_by_id(
    pointcloud_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get point cloud by ID
    """
    pointcloud = get_pointcloud(db, pointcloud_id=pointcloud_id)
    if not pointcloud:
        raise HTTPException(status_code=404, detail="Point cloud not found")
    if pointcloud.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return pointcloud


@router.get("/{pointcloud_id}/stats", response_model=PointCloudStats)
def get_pointcloud_statistics(
    pointcloud_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get point cloud statistics
    """
    pointcloud = get_pointcloud(db, pointcloud_id=pointcloud_id)
    if not pointcloud:
        raise HTTPException(status_code=404, detail="Point cloud not found")
    if pointcloud.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    stats = get_pointcloud_stats(db, pointcloud_id)
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to get point cloud statistics")
    return stats


@router.post("/{pointcloud_id}/process", response_model=PointCloudProcess)
def process_pointcloud_endpoint(
    pointcloud_id: int,
    process_config: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Process a point cloud with the given configuration
    """
    pointcloud = get_pointcloud(db, pointcloud_id=pointcloud_id)
    if not pointcloud:
        raise HTTPException(status_code=404, detail="Point cloud not found")
    if pointcloud.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create a job for processing
    from services.job_service import create_job
    job = create_job(
        db=db,
        job={
            "name": f"Process point cloud {pointcloud.name}",
            "description": f"Processing point cloud with config: {process_config}",
            "job_type": "pointcloud_processing",
            "parameters": process_config
        },
        owner_id=current_user.id
    )
    
    # Start processing in background
    background_tasks.add_task(
        process_pointcloud_job,
        job_id=job.id,
        pointcloud_id=pointcloud_id,
        config=process_config,
        db=db
    )
    
    return PointCloudProcess(
        status="processing",
        job_id=job.id,
        message="Point cloud processing started"
    )


@router.delete("/{pointcloud_id}")
def delete_pointcloud_by_id(
    pointcloud_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete point cloud
    """
    pointcloud = get_pointcloud(db, pointcloud_id=pointcloud_id)
    if not pointcloud:
        raise HTTPException(status_code=404, detail="Point cloud not found")
    if pointcloud.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = delete_pointcloud(db, pointcloud_id=pointcloud_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete point cloud")
    return {"message": "Point cloud deleted successfully"}


async def process_pointcloud_job(job_id: str, pointcloud_id: int, config: dict, db: Session):
    """Background task to process point cloud"""
    from services.job_service import start_job, complete_job, fail_job, update_job_progress
    
    try:
        start_job(db, job_id)
        update_job_progress(db, job_id, 10, "Starting point cloud processing...")
        
        # Simulate processing steps
        update_job_progress(db, job_id, 30, "Reading point cloud data...")
        # Add actual PDAL processing here
        
        update_job_progress(db, job_id, 60, "Applying filters...")
        # Add actual processing here
        
        update_job_progress(db, job_id, 90, "Generating outputs...")
        # Add output generation here
        
        result = {"processed": True, "output_path": "/path/to/output"}
        complete_job(db, job_id, result)
        
    except Exception as e:
        fail_job(db, job_id, str(e))
