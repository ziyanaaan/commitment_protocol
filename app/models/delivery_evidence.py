"""
Delivery evidence model for storing validation artifacts.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DeliveryEvidence(Base):
    """
    Evidence submitted with a delivery for validation.
    
    Types:
    - github: Link to a GitHub repository
    - screenshot: Link to an image file
    
    Each delivery can have multiple evidences (1-5).
    Settlement requires at least 1 validated evidence.
    """
    __tablename__ = "delivery_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to delivery
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False, index=True)
    
    # Evidence type: github | screenshot
    type = Column(String(20), nullable=False)
    
    # URL to the evidence
    url = Column(Text, nullable=False)
    
    # Validation metadata (JSON for flexibility)
    # For GitHub: full_name, stars, forks, open_issues, pushed_at, default_branch
    # For Screenshot: content_type, content_length, host
    # Note: Named 'evidence_metadata' to avoid conflict with SQLAlchemy's 'metadata' attribute
    evidence_metadata = Column("metadata", JSON, nullable=True)

    
    # Validation status
    validated = Column(Boolean, default=False, nullable=False)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
