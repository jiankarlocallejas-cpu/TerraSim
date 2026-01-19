from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import Base

class PointCloud(Base):
    __tablename__ = "pointclouds"

    name = Column(String, index=True)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    point_count = Column(Integer)
    bounds = Column(JSON)  # {"minx": float, "miny": float, "maxx": float, "maxy": float, "minz": float, "maxz": float}
    srs = Column(String)  # Spatial Reference System
    metadata = Column(JSON, default=dict)
    status = Column(String, default="uploaded")  # uploaded, processing, processed, error
    project_id = Column(Integer, ForeignKey("projects.id"))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="pointclouds")
    owner = relationship("User")
