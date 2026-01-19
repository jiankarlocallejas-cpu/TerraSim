from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Project(Base):
    __tablename__ = "projects"

    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    status = Column(String, default="active")  # active, archived, deleted
    metadata = Column(JSON, default=dict)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="projects")
    pointclouds = relationship("PointCloud", back_populates="project")
    rasters = relationship("Raster", back_populates="project")
    analyses = relationship("Analysis", back_populates="project")
