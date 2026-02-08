"""
Webhook Processor.

Background processor that reads unprocessed webhook events
and processes them safely inside transactions.

CRITICAL RULES:
- Use row-level locking (SELECT FOR UPDATE)
- Mark processed=true only after success
- Handle payment, payout, and refund events
- Never process the same event twice

Supported events:
- payment.captured
- payout.processed
- payout.failed
- payout.reversed
- refund.processed
- refund.failed
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.financial.webhook_event import WebhookEvent
from app.services.financial.payment_capture import (
    process_payment_captured,
    PaymentNotFound,
    PaymentAlreadyCaptured,
)


class WebhookProcessingError(Exception):
    """Base exception for webhook processing errors."""
    pass


def get_unprocessed_events(
    db: Session,
    limit: int = 100,
) -> List[WebhookEvent]:
    """
    Get unprocessed webhook events.
    
    Returns events in FIFO order (oldest first).
    """
    return (
        db.query(WebhookEvent)
        .filter(WebhookEvent.processed == False)
        .order_by(WebhookEvent.created_at)
        .limit(limit)
        .all()
    )


# Supported event types
SUPPORTED_EVENTS = {
    "payment.captured",
    "payout.processed",
    "payout.failed",
    "payout.reversed",
    "refund.processed",
    "refund.failed",
}


def process_webhook_event(
    db: Session,
    event_id,
) -> bool:
    """
    Process a single webhook event.
    
    Uses SELECT FOR UPDATE to prevent concurrent processing.
    
    Args:
        db: Database session
        event_id: The webhook event ID (UUID)
    
    Returns:
        True if processed successfully, False if skipped
    
    Raises:
        WebhookProcessingError: If processing fails
    """
    # Lock the event row
    event = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.id == event_id)
        .with_for_update(skip_locked=True)
        .first()
    )
    
    if not event:
        return False
    
    # Skip if already processed
    if event.processed:
        return False
    
    # Route to appropriate handler based on event type
    try:
        if event.event_type == "payment.captured":
            _handle_payment_captured(db, event)
        elif event.event_type == "payout.processed":
            _handle_payout_processed(db, event)
        elif event.event_type in ("payout.failed", "payout.reversed"):
            _handle_payout_failed(db, event)
        elif event.event_type == "refund.processed":
            _handle_refund_processed(db, event)
        elif event.event_type == "refund.failed":
            _handle_refund_failed(db, event)
        else:
            # Unsupported event - mark as processed and skip
            pass
        
        # Mark as processed
        event.processed = True
        event.processed_at = datetime.now(timezone.utc).isoformat()
        db.flush()
        
        return True
        
    except PaymentAlreadyCaptured:
        # Idempotent - already processed, mark as done
        event.processed = True
        event.processed_at = datetime.now(timezone.utc).isoformat()
        db.flush()
        return True
        
    except PaymentNotFound as e:
        # Payment doesn't exist - this might be a race condition
        # Leave unprocessed for retry
        raise WebhookProcessingError(f"Payment not found: {e}")
    
    except Exception as e:
        # Other errors - leave unprocessed
        raise WebhookProcessingError(f"Processing failed: {e}")


def _handle_payment_captured(
    db: Session,
    event: WebhookEvent,
) -> None:
    """
    Handle payment.captured event.
    
    Extracts payment info from Razorpay payload and processes capture.
    """
    payload = event.payload
    
    # Razorpay payment.captured payload structure:
    # {
    #   "event": "payment.captured",
    #   "payload": {
    #     "payment": {
    #       "entity": {
    #         "id": "pay_xxx",
    #         "amount": 50000,  # in paise
    #         "currency": "INR",
    #         ...
    #       }
    #     }
    #   }
    # }
    
    payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
    
    gateway_payment_id = payment_data.get("id")
    amount = payment_data.get("amount")  # Already in paise
    currency = payment_data.get("currency", "INR")
    
    if not gateway_payment_id or not amount:
        raise WebhookProcessingError(
            f"Missing payment data in event {event.gateway_event_id}"
        )
    
    # Process the capture
    process_payment_captured(
        db,
        gateway_payment_id=gateway_payment_id,
        captured_amount=amount,
        currency=currency,
        gateway_data=payment_data,
    )


def _handle_payout_processed(
    db: Session,
    event: WebhookEvent,
) -> None:
    """
    Handle payout.processed event.
    
    Marks payout as completed.
    """
    from app.services.financial.payout_executor import handle_payout_processed
    
    payload = event.payload
    payout_data = payload.get("payload", {}).get("payout", {}).get("entity", {})
    gateway_payout_id = payout_data.get("id")
    
    if gateway_payout_id:
        handle_payout_processed(db, gateway_payout_id)


def _handle_payout_failed(
    db: Session,
    event: WebhookEvent,
) -> None:
    """
    Handle payout.failed or payout.reversed event.
    
    Marks payout as failed and queues for retry.
    """
    from app.services.financial.payout_executor import handle_payout_failed
    
    payload = event.payload
    payout_data = payload.get("payload", {}).get("payout", {}).get("entity", {})
    gateway_payout_id = payout_data.get("id")
    failure_reason = payout_data.get("failure_reason", "")
    
    if gateway_payout_id:
        handle_payout_failed(db, gateway_payout_id, failure_reason)


def _handle_refund_processed(
    db: Session,
    event: WebhookEvent,
) -> None:
    """
    Handle refund.processed event.
    
    Marks refund as completed.
    """
    from app.services.financial.refund_executor import handle_refund_processed
    
    payload = event.payload
    refund_data = payload.get("payload", {}).get("refund", {}).get("entity", {})
    gateway_refund_id = refund_data.get("id")
    
    if gateway_refund_id:
        handle_refund_processed(db, gateway_refund_id)


def _handle_refund_failed(
    db: Session,
    event: WebhookEvent,
) -> None:
    """
    Handle refund.failed event.
    
    Marks refund as failed.
    """
    from app.services.financial.refund_executor import handle_refund_failed
    
    payload = event.payload
    refund_data = payload.get("payload", {}).get("refund", {}).get("entity", {})
    gateway_refund_id = refund_data.get("id")
    
    if gateway_refund_id:
        handle_refund_failed(db, gateway_refund_id)


def process_all_pending_events(
    db: Session,
    limit: int = 100,
) -> dict:
    """
    Process all pending webhook events.
    
    This is the main entry point for batch processing.
    
    Returns:
        Dict with processing stats
    """
    stats = {
        "processed": 0,
        "skipped": 0,
        "errors": [],
    }
    
    events = get_unprocessed_events(db, limit=limit)
    
    for event in events:
        try:
            # Each event in its own transaction
            success = process_webhook_event(db, event.id)
            if success:
                db.commit()
                stats["processed"] += 1
            else:
                stats["skipped"] += 1
        except WebhookProcessingError as e:
            db.rollback()
            stats["errors"].append({
                "event_id": str(event.id),
                "error": str(e),
            })
        except Exception as e:
            db.rollback()
            stats["errors"].append({
                "event_id": str(event.id),
                "error": str(e),
            })
    
    return stats
