"""
Raster Service - File I/O and processing for raster data
Provides raster-specific operations while delegating CRUD to data_service
"""

import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.raster import Raster
from schemas.raster import RasterCreate, RasterUpdate, RasterStats
from services.data_service import BaseDataService
import rasterio
import numpy as np

logger = logging.getLogger(__name__)


class RasterService(BaseDataService[Raster, RasterCreate, RasterUpdate]):
    """Service for raster data management"""
    
    def _prepare_create_data(self, item: RasterCreate, **kwargs) -> Dict[str, Any]:
        """Prepare raster data for creation"""
        return {
            'name': item.name,
            'file_path': item.file_path,
            'data_type': item.data_type,
            'resolution': item.resolution,
            'srs': item.srs,
            'bounds': item.bounds.dict() if item.bounds else None,
            'metadata': item.metadata,
        }
    
    def _prepare_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare raster data for update"""
        if "bounds" in data and data["bounds"]:
            data["bounds"] = data["bounds"].dict() if hasattr(data["bounds"], 'dict') else data["bounds"]
        return data


# Create singleton instance
_raster_service = RasterService(Raster)

# Expose convenience functions
def get_raster(db: Session, raster_id: int) -> Optional[Raster]:
    """Get a raster by ID"""
    return _raster_service.get_by_id(db, raster_id)


def get_rasters(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[Raster]:
    """Get rasters for owner"""
    return _raster_service.get_by_owner(db, owner_id, skip, limit)


def create_raster(db: Session, raster: RasterCreate, owner_id: int) -> Raster:
    """Create a new raster"""
    return _raster_service.create(db, raster, owner_id)


def update_raster(db: Session, raster_id: int, raster: RasterUpdate) -> Optional[Raster]:
    """Update a raster"""
    return _raster_service.update(db, raster_id, raster)


def delete_raster(db: Session, raster_id: int) -> bool:
    """Delete a raster"""
    return _raster_service.delete(db, raster_id)


async def process_raster_file(file_path: str, user_id: int, db: Session) -> Raster:
    """Process an uploaded raster file"""
    try:
        file_size = os.path.getsize(file_path)
        
        with rasterio.open(file_path) as src:
            bounds = {
                "minx": float(src.bounds.left),
                "miny": float(src.bounds.bottom),
                "maxx": float(src.bounds.right),
                "maxy": float(src.bounds.top),
            }
            
            resolution = float(abs(src.res[0]))
            srs = str(src.crs) if src.crs else None
            
            # Ensure bounds is a Bounds object
            bounds_obj = bounds
            if isinstance(bounds_obj, dict):
                from schemas.raster import Bounds as BoundsSchema
                bounds_obj = BoundsSchema(**bounds_obj)
            
            raster_data = RasterCreate(
                name=os.path.basename(file_path),
                file_path=file_path,
                srs=srs,
                resolution=resolution,
                bounds=bounds_obj,
                metadata={"original_filename": os.path.basename(file_path)}
            )
            
            db_raster = create_raster(db, raster_data, user_id)
            update_raster(db, db_raster.id, RasterUpdate(file_size=file_size, status="processed"))
            return db_raster
            
    except Exception as e:
        logger.error(f"Error processing raster: {e}")
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
            data = src.read(1, masked=True)
            
            # Ensure bounds is a Bounds object
            bounds_obj = raster.bounds
            if isinstance(bounds_obj, dict):
                from schemas.raster import Bounds as BoundsSchema
                bounds_obj = BoundsSchema(**bounds_obj)
            
            return RasterStats(
                file_size=raster.file_size or 0,
                width=src.width,
                height=src.height,
                resolution=raster.resolution or 0,
                bounds=bounds_obj,
                data_type=raster.data_type or "unknown",
                no_data_value=float(src.nodata) if src.nodata is not None else None,
                min_value=float(data.min()) if data.count() > 0 else None,
                max_value=float(data.max()) if data.count() > 0 else None,
                mean_value=float(data.mean()) if data.count() > 0 else None,
            )
    except Exception as e:
        logger.error(f"Error getting raster stats: {e}")
        return None


def create_cog(input_path: str, output_path: str) -> bool:
    """Create a Cloud Optimized GeoTIFF"""
    try:
        from rasterio.enums import Resampling
        
        with rasterio.open(input_path) as src:
            profile = src.profile
            profile.update({
                'driver': 'COG',
                'compress': 'DEFLATE',
                'tiled': True,
                'blockxsize': 256,
                'blockysize': 256,
            })
            
            with rasterio.open(output_path, 'w', **profile) as dst:
                for i in range(1, src.count + 1):
                    data = src.read(i, resampling=Resampling.nearest)
                    dst.write(data, i)
        
        return True
    except Exception as e:
        logger.error(f"Error creating COG: {e}")
        return False
