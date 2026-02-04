"""
Schemas for delivery evidence validation.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, HttpUrl, Field, field_validator
import re


class EvidenceItem(BaseModel):
    """Single evidence item for delivery validation."""
    
    type: Literal["github", "screenshot"] = Field(
        ..., description="Type of evidence: github or screenshot"
    )
    url: str = Field(
        ..., description="HTTPS URL to the evidence"
    )
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is HTTPS."""
        if not v.startswith("https://"):
            raise ValueError("URL must use HTTPS")
        return v


class DeliveryWithEvidenceCreate(BaseModel):
    """
    Request schema for delivery with evidence.
    Replaces the old DeliveryCreate for the /deliver endpoint.
    """
    evidences: List[EvidenceItem] = Field(
        ..., 
        min_length=1, 
        max_length=5,
        description="List of evidence items (1-5 required)"
    )


class EvidenceValidationResult(BaseModel):
    """Result of evidence validation."""
    type: str
    url: str
    validated: bool
    error: Optional[str] = None
    metadata: Optional[dict] = None


class DeliveryWithEvidenceResponse(BaseModel):
    """Response schema for delivery with evidence."""
    id: int
    status: str
    delivered_at: str
    evidence_count: int
    validated_count: int
    settlement_id: Optional[int] = None
    message: Optional[str] = None
