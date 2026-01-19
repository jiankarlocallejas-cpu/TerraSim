from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    last_login = Column(DateTime(timezone=True))
    preferences = Column(JSON, default=dict)

    # Relationships
    projects = relationship("Project", back_populates="owner")
    jobs = relationship("Job", back_populates="owner")
    analyses = relationship("Analysis", back_populates="owner")
