from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.session import get_db
from schemas.raster import Raster, RasterCreate, RasterProcess, RasterStats
from services.geospatial import (
    process_raster_file,
    get_rasters,
    get_raster,
    delete_raster,
    get_raster_stats,
    create_cog,
    create_raster
)
from api.deps import get_current_active_user
from core.config import settings
from schemas.user import User

router = APIRouter()


@router.post("/upload/", response_model=Raster)
async def upload_raster(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: int = None,
    data_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload a raster file (GeoTIFF, etc.)
    """
    if not file.filename.lower().endswith(('.tif', '.tiff', '.geotiff')):
        raise HTTPException(status_code=400, detail="File must be in GeoTIFF format")
    
    # Save file temporarily
    upload_dir = f"{settings.LOCAL_STORAGE_PATH}/uploads/rasters"
    os.makedirs(upload_dir, exist_ok=True)
    file_location = f"{upload_dir}/{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    
    # Create raster record
    raster_data = RasterCreate(
        name=file.filename,
        file_path=file_location,
        data_type=data_type
    )
    
    # Process in background
    background_tasks.add_task(
        process_raster_file,
        file_path=file_location,
        user_id=current_user.id,
        db=db
    )
    
    from services.geospatial import create_raster
    db_raster = create_raster(db, raster_data, current_user.id)
    
    return db_raster


@router.get("/", response_model=List[Raster])
def list_rasters(
    skip: int = 0, 
    limit: int = 100,
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all rasters for the current user
    """
    rasters = get_rasters(db, owner_id=current_user.id, skip=skip, limit=limit)
    
    # Filter by project if specified
    if project_id is not None:
        rasters = [r for r in rasters if r.project_id == project_id]
    
    return rasters


@router.get("/{raster_id}", response_model=Raster)
def get_raster_by_id(
    raster_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get raster by ID
    """
    raster = get_raster(db, raster_id=raster_id)
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")
    if raster.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return raster


@router.get("/{raster_id}/stats", response_model=RasterStats)
def get_raster_statistics(
    raster_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get raster statistics
    """
    raster = get_raster(db, raster_id=raster_id)
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")
    if raster.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    stats = get_raster_stats(db, raster_id)
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to get raster statistics")
    return stats


@router.post("/{raster_id}/process", response_model=RasterProcess)
def process_raster_endpoint(
    raster_id: int,
    process_config: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Process a raster with the given configuration
    """
    raster = get_raster(db, raster_id=raster_id)
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")
    if raster.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create a job for processing
    from services.job_service import create_job
    job = create_job(
        db=db,
        job={
            "name": f"Process raster {raster.name}",
            "description": f"Processing raster with config: {process_config}",
            "job_type": "raster_processing",
            "parameters": process_config
        },
        owner_id=current_user.id
    )
    
    # Start processing in background
    background_tasks.add_task(
        process_raster_job,
        job_id=job.id,
        raster_id=raster_id,
        config=process_config,
        db=db
    )
    
    return RasterProcess(
        status="processing",
        job_id=job.id,
        message="Raster processing started"
    )


@router.post("/{raster_id}/create-cog")
def create_cog_endpoint(
    raster_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a Cloud Optimized GeoTIFF (COG) from this raster
    """
    raster = get_raster(db, raster_id=raster_id)
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")
    if raster.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create COG in background
    cog_dir = f"{settings.LOCAL_STORAGE_PATH}/cogs"
    os.makedirs(cog_dir, exist_ok=True)
    cog_path = f"{cog_dir}/{raster.id}_cog.tif"
    
    background_tasks.add_task(
        create_cog_task,
        raster_id=raster_id,
        input_path=raster.file_path,
        output_path=cog_path,
        db=db
    )
    
    return {"message": "COG creation started", "output_path": cog_path}


@router.delete("/{raster_id}")
def delete_raster_by_id(
    raster_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete raster
    """
    raster = get_raster(db, raster_id=raster_id)
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")
    if raster.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = delete_raster(db, raster_id=raster_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete raster")
    return {"message": "Raster deleted successfully"}


async def process_raster_job(job_id: str, raster_id: int, config: dict, db: Session):
    """Background task to process raster"""
    from services.job_service import start_job, complete_job, fail_job, update_job_progress
    
    try:
        start_job(db, job_id)
        update_job_progress(db, job_id, 10, "Starting raster processing...")
        
        # Simulate processing steps
        update_job_progress(db, job_id, 30, "Reading raster data...")
        # Add actual GDAL processing here
        
        update_job_progress(db, job_id, 60, "Applying operations...")
        # Add actual processing here
        
        update_job_progress(db, job_id, 90, "Generating outputs...")
        # Add output generation here
        
        result = {"processed": True, "output_path": "/path/to/output"}
        complete_job(db, job_id, result)
        
    except Exception as e:
        fail_job(db, job_id, str(e))


async def create_cog_task(raster_id: int, input_path: str, output_path: str, db: Session):
    """Background task to create COG"""
    from services.geospatial import create_cog
    
    success = create_cog(input_path, output_path)
    
    # Update raster record with COG path
    if success:
        from services.geospatial import update_raster
        update_raster(db, raster_id, {"metadata": {"cog_path": output_path}})
