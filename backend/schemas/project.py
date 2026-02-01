from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: dict = {}


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class ProjectWithDetails(Project):
    pointclouds: List[dict] = []
    rasters: List[dict] = []
    analyses: List[dict] = []
