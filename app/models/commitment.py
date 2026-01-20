from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String
from sqlalchemy.sql import func
from app.core.database import Base


class Commitment(Base):
    __tablename__ = "commitments"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)


    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)

    deadline = Column(DateTime(timezone=True), nullable=False)

    decay_curve = Column(String, nullable=False)  # identifier, not logic

    status = Column(String, nullable=False, index=True)
    # draft | funded | locked | delivered | expired | settled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
