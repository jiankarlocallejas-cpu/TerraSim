from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class AnalysisBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # erosion, sediment, etc.
    parameters: Dict[str, Any] = {}


class AnalysisCreate(AnalysisBase):
    project_id: int


class AnalysisUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class Analysis(AnalysisBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    results: Dict[str, Any] = {}
    project_id: int
    owner_id: int

    class Config:
        from_attributes = True


class AnalysisResult(Analysis):
    pass


class ErosionAnalysisParameters(BaseModel):
    pointcloud_id: int
    raster_id: Optional[int] = None
    method: str = "m3c2"  # m3c2, simple_differencing, etc.
    parameters: Dict[str, Any] = {}


class ErosionAnalysisResults(BaseModel):
    total_volume_change: float
    mean_elevation_change: float
    std_elevation_change: float
    positive_volume: float  # deposition
    negative_volume: float  # erosion
    area_analyzed: float
    results_file_path: Optional[str] = None
    visualization_urls: Dict[str, str] = {}
