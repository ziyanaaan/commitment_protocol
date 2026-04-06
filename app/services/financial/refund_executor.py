"""
Refund Executor.

Background worker that processes created refunds.

CRITICAL SAFETY:
- Uses TRANSFERS_ENABLED flag
- SELECT FOR UPDATE SKIP LOCKED
- Never marks complete without webhook
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.services.financial.razorpay_client import (
    create_refund as api_create_refund,
    TransfersDisabledError,
)


logger = logging.getLogger(__name__)


class RefundExecutionError(Exception):
    """Error during refund execution."""
    pass


# ============================================================================
# Main Entry Point
# ============================================================================

def process_pending_refunds(
    db: Session,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Process pending refunds.
    
    This is the main entry point for the refund executor.
    Called by the background worker.
    
    Args:
        db: Database session
        limit: Maximum refunds to process in this batch
    
    Returns:
        Dict with processing stats
    """
    stats = {
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
    }
    
    # Check if transfers are enabled
    if not settings.TRANSFERS_ENABLED:
        logger.warning("Transfers disabled - skipping refund execution")
        return stats
    
    # Get created refunds with row locking
    refunds = _get_created_refunds(db, limit)
    
    for refund in refunds:
        try:
            result = execute_single_refund(db, refund["id"])
            if result["status"] == "processing":
                stats["processed"] += 1
            elif result["status"] == "skipped":
                stats["skipped"] += 1
            else:
                stats["failed"] += 1
                stats["errors"].append(result.get("error"))
            db.commit()
        except Exception as e:
            db.rollback()
            stats["failed"] += 1
            stats["errors"].append(str(e))
            logger.error(f"Refund {refund['id']} execution failed: {e}")
    
    return stats


def execute_single_refund(
    db: Session,
    refund_id: int,
) -> Dict[str, Any]:
    """
    Execute a single refund.
    
    Steps:
    1. Lock refund row
    2. Get original payment gateway ID
    3. Call Razorpay API
    4. Store gateway_refund_id
    5. Update status to 'pending_gateway'
    
    Args:
        db: Database session
        refund_id: Refund ID
    
    Returns:
        Dict with execution result
    """
    # Step 1: Lock and fetch refund
    refund = _lock_refund(db, refund_id)
    
    if not refund:
        return {"status": "not_found", "error": f"Refund {refund_id} not found"}
    
    # Skip if not in created status
    if refund["status"] != "created":
        return {"status": "skipped", "reason": f"Status is {refund['status']}"}
    
    # Step 2: Get original payment gateway ID
    payment = _get_payment(db, refund["payment_id"])
    
    if not payment:
        return {"status": "blocked", "error": "Original payment not found"}
    
    if not payment.get("gateway_payment_id"):
        return {"status": "blocked", "error": "Payment has no gateway ID"}
    
    # Step 3: Update status BEFORE API call
    _update_refund_status(db, refund_id, "pending_gateway")
    db.flush()
    
    # Step 4: Call Razorpay API
    try:
        response = api_create_refund(
            payment_id=payment["gateway_payment_id"],
            amount=refund["amount"],
        )
    except TransfersDisabledError:
        _update_refund_status(db, refund_id, "created")
        return {"status": "disabled", "error": "Transfers disabled"}
    
    # Step 5: Handle response
    if response.success:
        gateway_refund_id = response.data.get("id")
        _store_gateway_refund_id(db, refund_id, gateway_refund_id)
        logger.info(f"Refund {refund_id} sent to gateway: {gateway_refund_id}")
        return {
            "status": "processing",
            "gateway_refund_id": gateway_refund_id,
        }
    else:
        # API call failed
        _update_refund_status(db, refund_id, "failed")
        logger.error(f"Refund {refund_id} failed: {response.error}")
        return {
            "status": "failed",
            "error": response.error,
        }


# ============================================================================
# Internal Functions
# ============================================================================

def _get_created_refunds(db: Session, limit: int) -> List[Dict[str, Any]]:
    """Get created refunds with row locking (SKIP LOCKED)."""
    result = db.execute(
        text("""
            SELECT id, payment_id, commitment_id, amount, status,
                   gateway_refund_id
            FROM refunds
            WHERE status = 'created'
            ORDER BY created_at
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
        """),
        {"limit": limit}
    )
    return [dict(row._mapping) for row in result.fetchall()]


def _lock_refund(db: Session, refund_id: int) -> Optional[Dict[str, Any]]:
    """Lock and fetch a single refund."""
    result = db.execute(
        text("""
            SELECT id, payment_id, commitment_id, amount, status,
                   gateway_refund_id
            FROM refunds
            WHERE id = :refund_id
            FOR UPDATE
        """),
        {"refund_id": refund_id}
    )
    row = result.fetchone()
    return dict(row._mapping) if row else None


def _get_payment(db: Session, payment_id: Any) -> Optional[Dict[str, Any]]:
    """Get payment details including gateway ID."""
    result = db.execute(
        text("""
            SELECT id, gateway_payment_id, status, amount
            FROM payments
            WHERE id = :payment_id
        """),
        {"payment_id": payment_id}
    )
    row = result.fetchone()
    return dict(row._mapping) if row else None


def _update_refund_status(db: Session, refund_id: int, status: str) -> None:
    """Update refund status."""
    db.execute(
        text("""
            UPDATE refunds
            SET status = :status
            WHERE id = :refund_id
        """),
        {"refund_id": refund_id, "status": status}
    )


def _store_gateway_refund_id(db: Session, refund_id: int, gateway_id: str) -> None:
    """Store gateway refund ID."""
    db.execute(
        text("""
            UPDATE refunds
            SET gateway_refund_id = :gateway_id
            WHERE id = :refund_id
        """),
        {"refund_id": refund_id, "gateway_id": gateway_id}
    )


# ============================================================================
# Webhook Handlers
# ============================================================================

def handle_refund_processed(db: Session, gateway_refund_id: str) -> bool:
    """
    Handle refund.processed webhook.
    
    Marks refund as processed.
    """
    result = db.execute(
        text("""
            UPDATE refunds
            SET status = 'processed',
                processed_at = :now
            WHERE gateway_refund_id = :gateway_id
            AND status = 'pending_gateway'
            RETURNING id
        """),
        {"gateway_id": gateway_refund_id, "now": datetime.now(timezone.utc)}
    )
    row = result.fetchone()
    
    if row:
        logger.info(f"Refund {row[0]} processed via webhook")
        return True
    return False


def handle_refund_failed(db: Session, gateway_refund_id: str) -> bool:
    """
    Handle refund.failed webhook.
    
    Marks refund as failed.
    """
    result = db.execute(
        text("""
            UPDATE refunds
            SET status = 'failed'
            WHERE gateway_refund_id = :gateway_id
            AND status = 'pending_gateway'
            RETURNING id
        """),
        {"gateway_id": gateway_refund_id}
    )
    row = result.fetchone()
    
    if row:
        logger.error(f"Refund {row[0]} failed via webhook")
        return True
    return False
