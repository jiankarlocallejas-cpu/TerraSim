from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models"""
    pass

# Mixin for common columns
class TimestampedBase(Base):
    """Base class for all SQLAlchemy ORM models with common columns"""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Keep BaseModel as an alias for backwards compatibility
BaseModel = TimestampedBase
