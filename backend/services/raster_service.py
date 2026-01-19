import os
import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.raster import Raster
from schemas.raster import RasterCreate, RasterUpdate, RasterStats
from core.config import settings
import rasterio
import numpy as np

logger = logging.getLogger(__name__)


def get_raster(db: Session, raster_id: int) -> Optional[Raster]:
    """Get a raster by ID"""
    return db.query(Raster).filter(Raster.id == raster_id).first()


def get_rasters(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Raster]:
    """Get a list of rasters for a specific owner"""
    return (
        db.query(Raster)
        .filter(Raster.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_raster(db: Session, raster: RasterCreate, owner_id: int) -> Raster:
    """Create a new raster record"""
    db_raster = Raster(
        name=raster.name,
        file_path=raster.file_path,
        data_type=raster.data_type,
        resolution=raster.resolution,
        srs=raster.srs,
        bounds=raster.bounds.dict() if raster.bounds else None,
        metadata=raster.metadata,
        owner_id=owner_id,
    )
    db.add(db_raster)
    db.commit()
    db.refresh(db_raster)
    return db_raster


def update_raster(db: Session, raster_id: int, raster: RasterUpdate) -> Optional[Raster]:
    """Update a raster"""
    db_raster = get_raster(db, raster_id=raster_id)
    if not db_raster:
        return None
    
    update_data = raster.dict(exclude_unset=True)
    if "bounds" in update_data and update_data["bounds"]:
        update_data["bounds"] = update_data["bounds"].dict()
    
    for field, value in update_data.items():
        setattr(db_raster, field, value)
    
    db.commit()
    db.refresh(db_raster)
    return db_raster


def delete_raster(db: Session, raster_id: int) -> bool:
    """Delete a raster"""
    db_raster = get_raster(db, raster_id=raster_id)
    if not db_raster:
        return False
    
    # Delete the file from storage
    if os.path.exists(db_raster.file_path):
        os.remove(db_raster.file_path)
    
    db.delete(db_raster)
    db.commit()
    return True


async def process_raster_file(file_path: str, user_id: int, db: Session) -> Raster:
    """Process an uploaded raster file"""
    try:
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Read raster metadata
        with rasterio.open(file_path) as src:
            # Get bounds
            bounds = {
                "minx": float(src.bounds.left),
                "miny": float(src.bounds.bottom),
                "maxx": float(src.bounds.right),
                "maxy": float(src.bounds.top),
            }
            
            # Get resolution
            resolution = float(abs(src.res[0]))  # Use x resolution
            
            # Get SRS info
            srs = str(src.crs) if src.crs else None
            
            # Create raster record
            raster_data = RasterCreate(
                name=os.path.basename(file_path),
                file_path=file_path,
                srs=srs,
                resolution=resolution,
                bounds=bounds,
                metadata={"original_filename": os.path.basename(file_path)}
            )
            
            db_raster = create_raster(db, raster_data, user_id)
            
            # Update with processed data
            update_data = RasterUpdate(
                file_size=file_size,
                status="processed"
            )
            update_raster(db, db_raster.id, update_data)
            
            return db_raster
            
    except Exception as e:
        logger.error(f"Error processing raster file {file_path}: {str(e)}")
        # Create record with error status
        raster_data = RasterCreate(
            name=os.path.basename(file_path),
            file_path=file_path,
            metadata={"error": str(e)}
        )
        db_raster = create_raster(db, raster_data, user_id)
        update_raster(db, db_raster.id, RasterUpdate(status="error"))
        return db_raster


def get_raster_stats(db: Session, raster_id: int) -> Optional[RasterStats]:
    """Get statistics for a raster"""
    raster = get_raster(db, raster_id)
    if not raster:
        return None
    
    try:
        with rasterio.open(raster.file_path) as src:
            # Read a sample of the data for stats
            data = src.read(1, masked=True)
            
            # Calculate stats
            stats = {
                "min_value": float(data.min()) if data.count() > 0 else None,
                "max_value": float(data.max()) if data.count() > 0 else None,
                "mean_value": float(data.mean()) if data.count() > 0 else None,
            }
            
            return RasterStats(
                file_size=raster.file_size or 0,
                width=src.width,
                height=src.height,
                resolution=raster.resolution or 0,
                bounds=raster.bounds,
                data_type=raster.data_type or "unknown",
                no_data_value=float(src.nodata) if src.nodata is not None else None,
                **stats
            )
            
    except Exception as e:
        logger.error(f"Error getting raster stats: {str(e)}")
        return None


def create_cog(input_path: str, output_path: str) -> bool:
    """Create a Cloud Optimized GeoTIFF from a regular GeoTIFF"""
    try:
        import rasterio
        from rasterio.enums import Resampling
        
        # Read the source file
        with rasterio.open(input_path) as src:
            profile = src.profile
            
            # Update profile for COG
            profile.update({
                'driver': 'COG',
                'compress': 'DEFLATE',
                'tiled': True,
                'blockxsize': 256,
                'blockysize': 256,
            })
            
            # Write the COG
            with rasterio.open(output_path, 'w', **profile) as dst:
                for i in range(1, src.count + 1):
                    data = src.read(i, resampling=Resampling.nearest)
                    dst.write(data, i)
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating COG: {str(e)}")
        return False
