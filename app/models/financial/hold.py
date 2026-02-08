"""
Hold ORM Model - Escrow layer for payments.
"""

from sqlalchemy import Column, String, BigInteger, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class Hold(Base):
    """
    Escrow holds for committed payments.
    
    When a client pays, funds go into a hold.
    Holds can be partially released (payout) or refunded.
    """
    __tablename__ = "holds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    payment_id = Column(UUID(as_uuid=True), nullable=False)
    commitment_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Amount in smallest currency unit
    total_amount = Column(BigInteger, nullable=False)
    released_amount = Column(BigInteger, nullable=False, default=0)
    refunded_amount = Column(BigInteger, nullable=False, default=0)
    
    # Valid: active, partially_released, released, consumed, refunded
    status = Column(String, nullable=False)
    
    created_at = Column(String, server_default=func.now())
    released_at = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Hold {self.id}: {self.status} {self.total_amount}>"
    
    @property
    def available_amount(self) -> int:
        """Amount still available for release or refund."""
        return self.total_amount - self.released_amount - self.refunded_amount
