from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from .base import BaseModel

class PointCloud(BaseModel):
    __tablename__ = "pointclouds"

    name: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(nullable=True)  # in bytes
    point_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    bounds: Mapped[dict] = mapped_column(String, default=dict)  # {"minx": float, "miny": float, "maxx": float, "maxy": float, "minz": float, "maxz": float}
    srs: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Spatial Reference System
    pointcloud_metadata: Mapped[dict] = mapped_column(String, default=dict)
    status: Mapped[str] = mapped_column(String, default="uploaded")  # uploaded, processing, processed, error
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="pointclouds")
    owner: Mapped["User"] = relationship("User")
