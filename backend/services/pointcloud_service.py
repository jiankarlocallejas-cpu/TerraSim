import os
import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.pointcloud import PointCloud
from schemas.pointcloud import PointCloudCreate, PointCloudUpdate, PointCloudStats
from core.config import settings
import numpy as np

logger = logging.getLogger(__name__)


def get_pointcloud(db: Session, pointcloud_id: int) -> Optional[PointCloud]:
    """Get a point cloud by ID"""
    return db.query(PointCloud).filter(PointCloud.id == pointcloud_id).first()


def get_pointclouds(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[PointCloud]:
    """Get a list of point clouds for a specific owner"""
    return (
        db.query(PointCloud)
        .filter(PointCloud.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_pointcloud(db: Session, pointcloud: PointCloudCreate, owner_id: int) -> PointCloud:
    """Create a new point cloud record"""
    db_pointcloud = PointCloud(
        name=pointcloud.name,
        file_path=pointcloud.file_path,
        srs=pointcloud.srs,
        bounds=pointcloud.bounds.dict() if pointcloud.bounds else None,
        metadata=pointcloud.metadata,
        owner_id=owner_id,
    )
    db.add(db_pointcloud)
    db.commit()
    db.refresh(db_pointcloud)
    return db_pointcloud


def update_pointcloud(db: Session, pointcloud_id: int, pointcloud: PointCloudUpdate) -> Optional[PointCloud]:
    """Update a point cloud"""
    db_pointcloud = get_pointcloud(db, pointcloud_id=pointcloud_id)
    if not db_pointcloud:
        return None
    
    update_data = pointcloud.dict(exclude_unset=True)
    if "bounds" in update_data and update_data["bounds"]:
        update_data["bounds"] = update_data["bounds"].dict()
    
    for field, value in update_data.items():
        setattr(db_pointcloud, field, value)
    
    db.commit()
    db.refresh(db_pointcloud)
    return db_pointcloud


def delete_pointcloud(db: Session, pointcloud_id: int) -> bool:
    """Delete a point cloud"""
    db_pointcloud = get_pointcloud(db, pointcloud_id=pointcloud_id)
    if not db_pointcloud:
        return False
    
    # Delete the file from storage
    if os.path.exists(db_pointcloud.file_path):
        os.remove(db_pointcloud.file_path)
    
    db.delete(db_pointcloud)
    db.commit()
    return True


async def process_pointcloud_file(file_path: str, user_id: int, db: Session) -> PointCloud:
    """Process an uploaded point cloud file"""
    try:
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Read point cloud metadata
        if file_path.endswith('.las') or file_path.endswith('.laz'):
            las = laspy.read(file_path)
            point_count = len(las.points)
            
            # Get bounds
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
            
            # Get SRS info
            srs = str(las.header.srs) if hasattr(las.header, 'srs') else None
            
            # Create point cloud record
            pointcloud_data = PointCloudCreate(
                name=os.path.basename(file_path),
                file_path=file_path,
                srs=srs,
                metadata={"original_filename": os.path.basename(file_path)}
            )
            
            db_pointcloud = create_pointcloud(db, pointcloud_data, user_id)
            
            # Update with processed data
            update_data = PointCloudUpdate(
                point_count=point_count,
                file_size=file_size,
                bounds=bounds,
                status="processed"
            )
            update_pointcloud(db, db_pointcloud.id, update_data)
            
            return db_pointcloud
            
    except Exception as e:
        logger.error(f"Error processing point cloud file {file_path}: {str(e)}")
        # Create record with error status
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
        # Read the file to get stats
        las = laspy.read(pointcloud.file_path)
        
        # Calculate density
        if pointcloud.bounds:
            area = (pointcloud.bounds["maxx"] - pointcloud.bounds["minx"]) * \
                   (pointcloud.bounds["maxy"] - pointcloud.bounds["miny"])
            density = len(las.points) / area if area > 0 else 0
        else:
            density = 0
        
        # Classification counts
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
        logger.error(f"Error getting point cloud stats: {str(e)}")
        return None
