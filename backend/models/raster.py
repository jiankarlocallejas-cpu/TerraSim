from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import Base

class Raster(Base):
    __tablename__ = "rasters"

    name = Column(String, index=True)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    data_type = Column(String)  # dem, dsm, dtm, etc.
    resolution = Column(Float)  # in meters
    bounds = Column(JSON)  # {"minx": float, "miny": float, "maxx": float, "maxy": float}
    srs = Column(String)  # Spatial Reference System
    metadata = Column(JSON, default=dict)
    status = Column(String, default="uploaded")  # uploaded, processing, processed, error
    project_id = Column(Integer, ForeignKey("projects.id"))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="rasters")
    owner = relationship("User")
