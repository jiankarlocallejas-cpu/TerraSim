from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Bounds(BaseModel):
    minx: float
    miny: float
    maxx: float
    maxy: float
    minz: Optional[float] = None
    maxz: Optional[float] = None


class PointCloudBase(BaseModel):
    name: Optional[str] = None
    file_path: Optional[str] = None
    srs: Optional[str] = None
    bounds: Optional[Bounds] = None
    metadata: Dict[str, Any] = {}


class PointCloudCreate(PointCloudBase):
    pass


class PointCloudUpdate(BaseModel):
    name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    point_count: Optional[int] = None
    srs: Optional[str] = None
    bounds: Optional[Bounds] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class PointCloud(PointCloudBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    file_path: str
    file_size: Optional[int] = None
    point_count: Optional[int] = None
    status: str
    project_id: Optional[int] = None
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class PointCloudProcess(BaseModel):
    status: str
    job_id: Optional[str] = None
    message: Optional[str] = None


class PointCloudStats(BaseModel):
    point_count: int
    file_size: int
    bounds: Bounds
    density: float  # points per square meter
    classification_counts: Dict[str, int] = {}
