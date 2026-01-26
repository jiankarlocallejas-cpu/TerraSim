from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from .base import BaseModel

class Project(BaseModel):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")  # active, archived, deleted
    project_metadata: Mapped[dict] = mapped_column(String, default=dict)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    pointclouds: Mapped[list] = relationship("PointCloud", back_populates="project")
    rasters: Mapped[list] = relationship("Raster", back_populates="project")
    analyses: Mapped[list] = relationship("Analysis", back_populates="project")
