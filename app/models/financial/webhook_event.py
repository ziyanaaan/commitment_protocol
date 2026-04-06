"""
WebhookEvent ORM Model - Gateway webhook deduplication.
"""

from sqlalchemy import Column, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class WebhookEvent(Base):
    """
    Webhook event record for idempotent processing.
    
    Stores gateway webhook events to prevent duplicate processing.
    """
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    # Unique gateway event identifier
    gateway_event_id = Column(String, nullable=False, unique=True)
    
    event_type = Column(String, nullable=False)
    
    # Raw webhook payload
    payload = Column(JSONB, nullable=False)
    
    processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(String, nullable=True)
    
    created_at = Column(String, server_default=func.now())
    
    def __repr__(self):
        return f"<WebhookEvent {self.gateway_event_id}: {self.event_type} processed={self.processed}>"
