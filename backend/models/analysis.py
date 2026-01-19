from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import Base

class Analysis(Base):
    __tablename__ = "analyses"

    name = Column(String, index=True)
    description = Column(Text)
    type = Column(String)  # erosion, sediment, etc.
    status = Column(String, default="pending")  # pending, running, completed, failed
    parameters = Column(JSON, default=dict)
    results = Column(JSON, default=dict)
    project_id = Column(Integer, ForeignKey("projects.id"))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="analyses")
    owner = relationship("User", back_populates="analyses")
    jobs = relationship("Job", back_populates="analysis")
