"""
Point Cloud Service - File I/O and processing for point cloud data
Provides point cloud-specific operations while delegating CRUD to data_service
"""

import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.pointcloud import PointCloud
from schemas.pointcloud import PointCloudCreate, PointCloudUpdate, PointCloudStats
from services.data_service import BaseDataService
import numpy as np

logger = logging.getLogger(__name__)


class PointCloudService(BaseDataService[PointCloud, PointCloudCreate, PointCloudUpdate]):
    """Service for point cloud data management"""
    
    def _prepare_create_data(self, pointcloud: PointCloudCreate, **kwargs) -> Dict[str, Any]:
        """Prepare point cloud data for creation"""
        file_path = pointcloud.file_path if hasattr(pointcloud, 'file_path') else None
        if not file_path:
            raise ValueError("Point cloud file path not provided")
        
        return {
            'name': pointcloud.name,
            'file_path': file_path,
            'srs': pointcloud.srs,
            'bounds': pointcloud.bounds.dict() if pointcloud.bounds else None,
            'metadata': pointcloud.metadata,
        }
    
    def _prepare_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare point cloud data for update"""
        if "bounds" in data and data["bounds"]:
            if isinstance(data["bounds"], dict):
                # Convert string keys to proper bounds format if needed
                pass
        return data


# Create singleton instance
_pointcloud_service = PointCloudService(PointCloud)

# Expose convenience functions
def get_pointcloud(db: Session, pointcloud_id: int) -> Optional[PointCloud]:
    """Get a point cloud by ID"""
    return _pointcloud_service.get_by_id(db, pointcloud_id)


def get_pointclouds(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[PointCloud]:
    """Get point clouds for owner"""
    return _pointcloud_service.get_by_owner(db, owner_id, skip, limit)


def create_pointcloud(db: Session, pointcloud: PointCloudCreate, owner_id: int) -> PointCloud:
    """Create a new point cloud"""
    return _pointcloud_service.create(db, pointcloud, owner_id)


def update_pointcloud(db: Session, pointcloud_id: int, pointcloud: PointCloudUpdate) -> Optional[PointCloud]:
    """Update a point cloud"""
    return _pointcloud_service.update(db, pointcloud_id, pointcloud)


def delete_pointcloud(db: Session, pointcloud_id: int) -> bool:
    """Delete a point cloud"""
    return _pointcloud_service.delete(db, pointcloud_id)


async def process_pointcloud_file(file_path: str, user_id: int, db: Session) -> PointCloud:
    """Process an uploaded point cloud file"""
    try:
        file_size = os.path.getsize(file_path)
        
        if file_path.endswith('.las') or file_path.endswith('.laz'):
            try:
                import laspy
            except ImportError:
                raise ImportError("laspy not installed. Install with: pip install laspy")
            
            las = laspy.read(file_path)
            point_count = len(las.points)
            
            mins = las.header.min
            maxs = las.header.max
            bounds = {
                "minx": float(mins[0]),
                "miny": float(mins[1]),
                "maxx": float(maxs[0]),
                "maxy": float(maxs[1]),
                "minz": float(mins[2]) if len(mins) > 2 else None,
                "maxz": float(maxs[2]) if len(maxs) > 2 else None,
            }
            
            srs = str(las.header.srs) if hasattr(las.header, 'srs') else None
            
            pointcloud_data = PointCloudCreate(
                name=os.path.basename(file_path),
                file_path=file_path,
                srs=srs,
                metadata={"original_filename": os.path.basename(file_path)}
            )
            
            db_pointcloud = create_pointcloud(db, pointcloud_data, user_id)
            update_pointcloud(db, db_pointcloud.id, PointCloudUpdate(
                point_count=point_count,
                file_size=file_size,
                bounds=bounds,
                status="processed"
            ))
            return db_pointcloud
            
    except Exception as e:
        logger.error(f"Error processing point cloud: {e}")
        pointcloud_data = PointCloudCreate(
            name=os.path.basename(file_path),
            file_path=file_path,
            metadata={"error": str(e)}
        )
        db_pointcloud = create_pointcloud(db, pointcloud_data, user_id)
        update_pointcloud(db, db_pointcloud.id, PointCloudUpdate(status="error"))
        return db_pointcloud


def get_pointcloud_stats(db: Session, pointcloud_id: int) -> Optional[PointCloudStats]:
    """Get statistics for a point cloud"""
    pointcloud = get_pointcloud(db, pointcloud_id)
    if not pointcloud:
        return None
    
    try:
        try:
            import laspy
        except ImportError:
            raise ImportError("laspy not installed. Install with: pip install laspy")
        
        las = laspy.read(pointcloud.file_path)
        
        if pointcloud.bounds:
            area = (pointcloud.bounds["maxx"] - pointcloud.bounds["minx"]) * \
                   (pointcloud.bounds["maxy"] - pointcloud.bounds["miny"])
            density = len(las.points) / area if area > 0 else 0
        else:
            density = 0
        
        classification_counts = {}
        if hasattr(las, 'classification'):
            classifications = las.classification
            unique, counts = np.unique(classifications, return_counts=True)
            classification_counts = dict(zip(unique.tolist(), counts.tolist()))
        
        return PointCloudStats(
            point_count=len(las.points),
            file_size=pointcloud.file_size or 0,
            bounds=pointcloud.bounds,
            density=density,
            classification_counts=classification_counts
        )
        
    except Exception as e:
        logger.error(f"Error getting point cloud stats: {e}")
        return None

