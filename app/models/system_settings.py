"""
System settings model for kill switches and configuration.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class SystemSetting(Base):
    """
    Key-value store for system settings and kill switches.
    
    Known keys:
    - payouts_paused: If true, all payouts are paused
    - refunds_paused: If true, all refunds are paused
    - all_transfers_paused: If true, all transfers are paused
    """
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Setting key (unique)
    key = Column(String(100), unique=True, nullable=False, index=True)
    
    # Boolean value
    value = Column(Boolean, nullable=False, default=False)
    
    # Description
    description = Column(String(500), nullable=True)
    
    # Audit trail
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
