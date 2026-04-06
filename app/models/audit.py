"""
Audit log model for security event tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    Audit log for tracking security-related events.
    
    Event types:
    - signup: User account creation
    - login: Successful login
    - login_failed: Failed login attempt
    - logout: User logout
    - token_refresh: Token rotation
    - password_change: Password changed
    - account_locked: Account locked due to failed attempts
    - account_unlocked: Account unlocked (manual or automatic)
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Can be null for failed login attempts on non-existent users
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Event classification
    event_type = Column(String(50), nullable=False, index=True)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(String(500), nullable=True)
    
    # Additional event details (JSON for flexibility)
    details = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
