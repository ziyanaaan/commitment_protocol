from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric
from sqlalchemy.sql import func
from app.core.database import Base


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)

    commitment_id = Column(Integer, ForeignKey("commitments.id"), nullable=False, unique=True)

    delay_minutes = Column(Integer, nullable=False)

    payout_amount = Column(Numeric(10, 2), nullable=False)
    refund_amount = Column(Numeric(10, 2), nullable=False)

    settled_at = Column(DateTime(timezone=True), server_default=func.now())
