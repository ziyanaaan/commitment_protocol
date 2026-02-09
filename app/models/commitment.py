from sqlalchemy import Column, Integer, DateTime, Numeric, String
from sqlalchemy.sql import func
from app.core.database import Base


class Commitment(Base):
    __tablename__ = "commitments"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)

    # Changed from Integer ForeignKey to String(40) for public_id
    client_id = Column(String(40), nullable=False, index=True)
    freelancer_id = Column(String(40), nullable=False, index=True)

    amount = Column(Numeric(10, 2), nullable=False)

    deadline = Column(DateTime(timezone=True), nullable=False)

    decay_curve = Column(String(20), nullable=False, default="balanced")  # identifier, not logic

    status = Column(String, nullable=False, index=True)
    # draft | funded | locked | delivered | expired | settled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
