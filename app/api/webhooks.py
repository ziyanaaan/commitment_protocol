"""
Razorpay Webhook API Endpoint.

CRITICAL RULES:
- Verify signature before storing
- Store event immediately
- Return 200 quickly
- Do NOT run business logic inside request
"""

import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.config import settings
from app.models.financial.webhook_event import WebhookEvent


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_razorpay_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify Razorpay webhook signature.
    
    Razorpay uses HMAC SHA256 for webhook signatures.
    """
    expected = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive Razorpay webhook events.
    
    This endpoint:
    1. Verifies the webhook signature
    2. Stores the event in webhook_events table
    3. Returns 200 immediately
    
    Business logic is processed separately by the webhook processor.
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Get signature header
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    # Verify signature
    webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "")
    if webhook_secret and not verify_razorpay_signature(body, signature, webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    
    # Parse payload
    try:
        import json
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    
    # Extract event info
    event_id = payload.get("event_id") or payload.get("id")
    event_type = payload.get("event")
    
    if not event_id or not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event_id or event type",
        )
    
    # Store event (idempotent - unique constraint on gateway_event_id)
    try:
        webhook_event = WebhookEvent(
            gateway_event_id=event_id,
            event_type=event_type,
            payload=payload,
            processed=False,
        )
        db.add(webhook_event)
        db.commit()
    except IntegrityError:
        # Event already exists (duplicate webhook)
        db.rollback()
        # Still return 200 to acknowledge receipt
    
    # Return 200 immediately
    return {"status": "received"}
