"""
Financial ledger model for tracking all money movement.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.core.database import Base


class LedgerEntry(Base):
    """
    Immutable ledger entry for financial audit trail.
    
    Entry types:
    - payment_in: Client payment received
    - payout: Freelancer payout
    - refund: Client refund
    - fee: Platform fee
    - adjustment: Manual adjustment by admin
    """
    __tablename__ = "ledger_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Related entities (nullable - not all entries relate to all entities)
    commitment_id = Column(Integer, ForeignKey("commitments.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Entry classification
    entry_type = Column(String(30), nullable=False, index=True)  # payment_in | payout | refund | fee | adjustment
    
    # Financial data
    amount = Column(Numeric(12, 2), nullable=False)  # Positive or negative
    running_balance = Column(Numeric(12, 2), nullable=False)  # Platform balance after this entry
    
    # Reference to source record
    reference_type = Column(String(30), nullable=True)  # payment | settlement | manual
    reference_id = Column(Integer, nullable=True)  # ID of the referenced record
    
    # Description for adjustments
    description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
