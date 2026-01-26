from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional
from .base import Base, BaseModel

class Job(Base, BaseModel):
    __tablename__ = "jobs"

    name: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, running, completed, failed, cancelled
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict] = mapped_column(String, default=dict)
    result: Mapped[dict] = mapped_column(String, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    job_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # pointcloud_processing, raster_analysis, etc.
    analysis_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analyses.id"), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="jobs")
    owner: Mapped["User"] = relationship("User", back_populates="jobs")
