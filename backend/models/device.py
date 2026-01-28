"""
Device Tracking Models
Store device information and login history
"""

from sqlalchemy import Boolean, String, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional
from .base import BaseModel
import uuid


class Device(BaseModel):
    """User device information"""
    __tablename__ = "devices"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    device_name: Mapped[str] = mapped_column(String, nullable=False)  # "Windows 10 - Chrome"
    os: Mapped[str] = mapped_column(String, nullable=False)  # "Windows", "Linux", "macOS"
    browser: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    login_events: Mapped[list] = relationship("LoginEvent", back_populates="device", cascade="all, delete-orphan")


class LoginEvent(BaseModel):
    """Login and signup audit trail"""
    __tablename__ = "login_events"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)  # "login", "signup", "logout", "failed_login"
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # "invalid_password", "account_locked", etc.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="login_events")


class EmailVerification(BaseModel):
    """Email verification records"""
    __tablename__ = "email_verifications"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
