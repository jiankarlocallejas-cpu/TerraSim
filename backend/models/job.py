from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class Job(Base):
    __tablename__ = "jobs"

    name = Column(String, index=True)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 0-100
    logs = Column(Text)
    parameters = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    job_type = Column(String)  # pointcloud_processing, raster_analysis, etc.
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="jobs")
    owner = relationship("User", back_populates="jobs")
