"""
Admin audit log model for tracking admin actions.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class AdminAuditLog(Base):
    """
    Audit log for tracking admin-specific actions.
    
    Action types:
    - payout_retry: Admin retried a failed payout
    - refund_manual: Admin initiated manual refund
    - kill_switch_toggle: Admin toggled a kill switch
    - setting_update: Admin updated a system setting
    - commitment_view: Admin viewed commitment financial details
    - ledger_view: Admin viewed ledger entries
    """
    __tablename__ = "admin_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Admin who performed the action
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Action classification
    action_type = Column(String(50), nullable=False, index=True)
    
    # Target entity
    target_type = Column(String(50), nullable=True)  # commitment | payout | refund | setting
    target_id = Column(Integer, nullable=True)
    
    # Additional details (JSON for flexibility)
    details = Column(JSON, nullable=True)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
