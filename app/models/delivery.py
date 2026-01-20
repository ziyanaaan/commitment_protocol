from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)

    commitment_id = Column(Integer, ForeignKey("commitments.id"), nullable=False, unique=True)

    artifact_type = Column(String, nullable=False)
    # file | link | repo | text

    artifact_reference = Column(String, nullable=False)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
