from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Bounds(BaseModel):
    minx: float
    miny: float
    maxx: float
    maxy: float


class RasterBase(BaseModel):
    name: Optional[str] = None
    file_path: Optional[str] = None
    data_type: Optional[str] = None  # dem, dsm, dtm, etc.
    resolution: Optional[float] = None  # in meters
    srs: Optional[str] = None
    bounds: Optional[Bounds] = None
    metadata: Dict[str, Any] = {}


class RasterCreate(RasterBase):
    pass


class RasterUpdate(BaseModel):
    name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    data_type: Optional[str] = None
    resolution: Optional[float] = None
    srs: Optional[str] = None
    bounds: Optional[Bounds] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class Raster(RasterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    file_path: str
    file_size: Optional[int] = None
    status: str
    project_id: Optional[int] = None
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class RasterProcess(BaseModel):
    status: str
    job_id: Optional[str] = None
    message: Optional[str] = None


class RasterStats(BaseModel):
    file_size: int
    width: int
    height: int
    resolution: float
    bounds: Bounds
    data_type: str
    no_data_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
