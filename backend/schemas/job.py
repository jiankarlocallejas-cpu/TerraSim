from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class JobBase(BaseModel):
    name: str
    description: Optional[str] = None
    job_type: str  # pointcloud_processing, raster_analysis, etc.
    parameters: Dict[str, Any] = {}


class JobCreate(JobBase):
    analysis_id: Optional[int] = None


class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    logs: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class Job(JobBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    progress: int
    logs: Optional[str] = None
    result: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    analysis_id: Optional[int] = None
    owner_id: int

    class Config:
        orm_mode = True


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
