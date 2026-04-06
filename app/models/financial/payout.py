"""
Payout ORM Model - Money leaving platform to freelancers.
"""

from sqlalchemy import Column, String, BigInteger, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class Payout(Base):
    """
    Payout record for money leaving the platform.
    
    Created when freelancer is owed money after settlement.
    Starts in 'queued' status, processed by payout executor.
    """
    __tablename__ = "payouts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    commitment_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Amount in smallest currency unit
    amount = Column(BigInteger, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    
    # Valid: queued, processing, completed, failed, retrying, reversed
    status = Column(String, nullable=False)
    
    # Gateway reference (populated after processing)
    gateway_payout_id = Column(String, nullable=True)
    
    # CRITICAL: Prevents duplicate payouts
    idempotency_key = Column(String, nullable=False, unique=True)
    
    retry_count = Column(Integer, nullable=False, default=0)
    
    created_at = Column(String, server_default=func.now())
    processed_at = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Payout {self.id}: {self.status} {self.amount}>"
