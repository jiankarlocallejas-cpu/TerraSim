from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from .base import BaseModel

class Analysis(BaseModel):
    __tablename__ = "analyses"

    name: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # erosion, sediment, etc.
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, running, completed, failed
    parameters: Mapped[dict] = mapped_column(String, default=dict)
    results: Mapped[dict] = mapped_column(String, default=dict)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="analyses")
    owner: Mapped["User"] = relationship("User", back_populates="analyses")
    jobs: Mapped[list] = relationship("Job", back_populates="analysis")
