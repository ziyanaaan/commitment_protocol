"""
Refund ORM Model - Money returning to clients.
"""

from sqlalchemy import Column, String, BigInteger, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class Refund(Base):
    """
    Refund record for money returning to client.
    
    Created when a commitment is cancelled or partially refunded.
    """
    __tablename__ = "refunds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    payment_id = Column(UUID(as_uuid=True), nullable=False)
    commitment_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Amount in smallest currency unit
    amount = Column(BigInteger, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    
    # Valid: created, pending_gateway, processed, failed
    status = Column(String, nullable=False)
    
    # Gateway reference (populated after processing)
    gateway_refund_id = Column(String, nullable=True)
    
    reason = Column(String, nullable=True)
    
    created_at = Column(String, server_default=func.now())
    processed_at = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Refund {self.id}: {self.status} {self.amount}>"
