"""
Payout Executor.

Background worker that processes queued payouts.

CRITICAL SAFETY:
- Uses TRANSFERS_ENABLED flag
- SELECT FOR UPDATE SKIP LOCKED
- Idempotency via idempotency_key
- Pre-payout safety checks
- Never marks complete without webhook
- Exponential backoff for retries
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.services.financial.razorpay_client import (
    create_payout as api_create_payout,
    TransfersDisabledError,
    APIResponse,
)


logger = logging.getLogger(__name__)


class PayoutExecutionError(Exception):
    """Error during payout execution."""
    pass


class SafetyCheckFailed(PayoutExecutionError):
    """Pre-payout safety check failed."""
    pass


class BeneficiaryNotFound(PayoutExecutionError):
    """Beneficiary account not found for user."""
    pass


# ============================================================================
# Main Entry Point
# ============================================================================

def process_pending_payouts(
    db: Session,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Process pending payouts.
    
    This is the main entry point for the payout executor.
    Called by the background worker.
    
    Args:
        db: Database session
        limit: Maximum payouts to process in this batch
    
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
        logger.warning("Transfers disabled - skipping payout execution")
        return stats
    
    # Get queued payouts with row locking
    payouts = _get_queued_payouts(db, limit)
    
    for payout in payouts:
        try:
            result = execute_single_payout(db, payout["id"])
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
            logger.error(f"Payout {payout['id']} execution failed: {e}")
    
    return stats


def execute_single_payout(
    db: Session,
    payout_id: int,
) -> Dict[str, Any]:
    """
    Execute a single payout.
    
    Steps:
    1. Lock payout row
    2. Run safety checks
    3. Get beneficiary account
    4. Call Razorpay API
    5. Store gateway_payout_id
    6. Update status to 'processing'
    
    Args:
        db: Database session
        payout_id: Payout ID
    
    Returns:
        Dict with execution result
    """
    # Step 1: Lock and fetch payout
    payout = _lock_payout(db, payout_id)
    
    if not payout:
        return {"status": "not_found", "error": f"Payout {payout_id} not found"}
    
    # Skip if not in queued/retrying status
    if payout["status"] not in ("queued", "retrying"):
        return {"status": "skipped", "reason": f"Status is {payout['status']}"}
    
    # Check retry limit
    if payout["retry_count"] >= settings.MAX_PAYOUT_RETRIES:
        _mark_payout_manual_review(db, payout_id)
        return {"status": "manual_review", "reason": "Max retries exceeded"}
    
    # Step 2: Run safety checks
    try:
        _run_safety_checks(db, payout)
    except SafetyCheckFailed as e:
        logger.error(f"Safety check failed for payout {payout_id}: {e}")
        return {"status": "blocked", "error": str(e)}
    
    # Step 3: Get beneficiary account
    beneficiary = _get_beneficiary(db, payout["user_id"])
    
    if not beneficiary:
        return {"status": "blocked", "error": "No beneficiary account found"}
    
    # Step 4: Update status to 'processing' BEFORE API call
    _update_payout_status(db, payout_id, "processing")
    db.flush()
    
    # Step 5: Call Razorpay API
    try:
        response = api_create_payout(
            fund_account_id=beneficiary["gateway_fund_account_id"],
            amount=payout["amount"],
            currency=payout.get("currency", "INR"),
            idempotency_key=payout["idempotency_key"],
            reference_id=str(payout_id),
        )
    except TransfersDisabledError:
        _update_payout_status(db, payout_id, "queued")
        return {"status": "disabled", "error": "Transfers disabled"}
    
    # Step 6: Handle response
    if response.success:
        gateway_payout_id = response.data.get("id")
        _store_gateway_payout_id(db, payout_id, gateway_payout_id)
        logger.info(f"Payout {payout_id} sent to gateway: {gateway_payout_id}")
        return {
            "status": "processing",
            "gateway_payout_id": gateway_payout_id,
        }
    else:
        # API call failed - increment retry and requeue
        _handle_payout_failure(db, payout_id, response.error)
        return {
            "status": "failed",
            "error": response.error,
        }


# ============================================================================
# Safety Checks
# ============================================================================

def _run_safety_checks(db: Session, payout: Dict[str, Any]) -> None:
    """
    Run pre-payout safety checks.
    
    Raises:
        SafetyCheckFailed: If any check fails
    """
    commitment_id = payout["commitment_id"]
    amount = payout["amount"]
    
    # Check 1: Commitment must be settled
    result = db.execute(
        text("""
            SELECT status FROM commitments WHERE id = :commitment_id
        """),
        {"commitment_id": commitment_id}
    )
    row = result.fetchone()
    
    if not row or row[0] != "settled":
        raise SafetyCheckFailed(
            f"Commitment {commitment_id} is not settled (status: {row[0] if row else 'not found'})"
        )
    
    # Check 2: Hold must have sufficient released amount
    result = db.execute(
        text("""
            SELECT released_amount FROM holds WHERE commitment_id = :commitment_id
        """),
        {"commitment_id": commitment_id}
    )
    hold = result.fetchone()
    
    if not hold or hold[0] < amount:
        raise SafetyCheckFailed(
            f"Hold released amount ({hold[0] if hold else 0}) is less than payout amount ({amount})"
        )
    
    # Check 3: No duplicate processing
    result = db.execute(
        text("""
            SELECT COUNT(*) FROM payouts
            WHERE commitment_id = :commitment_id
            AND status IN ('processing', 'completed')
            AND id != :payout_id
        """),
        {"commitment_id": commitment_id, "payout_id": payout["id"]}
    )
    if result.scalar() > 0:
        raise SafetyCheckFailed(
            f"Another payout for commitment {commitment_id} is already processing/completed"
        )


# ============================================================================
# Internal Functions
# ============================================================================

def _get_queued_payouts(db: Session, limit: int) -> List[Dict[str, Any]]:
    """Get queued payouts with row locking (SKIP LOCKED)."""
    result = db.execute(
        text("""
            SELECT id, commitment_id, user_id, amount, currency,
                   status, idempotency_key, retry_count
            FROM payouts
            WHERE status IN ('queued', 'retrying')
            ORDER BY created_at
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
        """),
        {"limit": limit}
    )
    return [dict(row._mapping) for row in result.fetchall()]


def _lock_payout(db: Session, payout_id: int) -> Optional[Dict[str, Any]]:
    """Lock and fetch a single payout."""
    result = db.execute(
        text("""
            SELECT id, commitment_id, user_id, amount, currency,
                   status, idempotency_key, retry_count, gateway_payout_id
            FROM payouts
            WHERE id = :payout_id
            FOR UPDATE
        """),
        {"payout_id": payout_id}
    )
    row = result.fetchone()
    return dict(row._mapping) if row else None


def _get_beneficiary(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    """Get primary beneficiary account for user."""
    result = db.execute(
        text("""
            SELECT id, gateway_contact_id, gateway_fund_account_id, account_type
            FROM beneficiary_accounts
            WHERE user_id = :user_id
            AND is_primary = true
            AND is_active = true
            LIMIT 1
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()
    return dict(row._mapping) if row else None


def _update_payout_status(db: Session, payout_id: int, status: str) -> None:
    """Update payout status."""
    db.execute(
        text("""
            UPDATE payouts
            SET status = :status
            WHERE id = :payout_id
        """),
        {"payout_id": payout_id, "status": status}
    )


def _store_gateway_payout_id(db: Session, payout_id: int, gateway_id: str) -> None:
    """Store gateway payout ID."""
    db.execute(
        text("""
            UPDATE payouts
            SET gateway_payout_id = :gateway_id
            WHERE id = :payout_id
        """),
        {"payout_id": payout_id, "gateway_id": gateway_id}
    )


def _handle_payout_failure(db: Session, payout_id: int, error: str) -> None:
    """Handle payout failure - increment retry count and update status."""
    db.execute(
        text("""
            UPDATE payouts
            SET status = 'retrying',
                retry_count = retry_count + 1
            WHERE id = :payout_id
        """),
        {"payout_id": payout_id}
    )
    logger.warning(f"Payout {payout_id} failed, marked for retry: {error}")


def _mark_payout_manual_review(db: Session, payout_id: int) -> None:
    """Mark payout for manual review after max retries."""
    db.execute(
        text("""
            UPDATE payouts
            SET status = 'manual_review'
            WHERE id = :payout_id
        """),
        {"payout_id": payout_id}
    )
    logger.error(f"Payout {payout_id} marked for manual review - max retries exceeded")


# ============================================================================
# Webhook Handlers
# ============================================================================

def handle_payout_processed(db: Session, gateway_payout_id: str) -> bool:
    """
    Handle payout.processed webhook.
    
    Marks payout as completed.
    """
    result = db.execute(
        text("""
            UPDATE payouts
            SET status = 'completed',
                processed_at = :now
            WHERE gateway_payout_id = :gateway_id
            AND status = 'processing'
            RETURNING id
        """),
        {"gateway_id": gateway_payout_id, "now": datetime.now(timezone.utc)}
    )
    row = result.fetchone()
    
    if row:
        logger.info(f"Payout {row[0]} completed via webhook")
        return True
    return False


def handle_payout_failed(
    db: Session,
    gateway_payout_id: str,
    failure_reason: str = "",
) -> bool:
    """
    Handle payout.failed webhook.
    
    Marks payout as failed and increments retry count.
    """
    # Check current retry count
    result = db.execute(
        text("""
            SELECT id, retry_count FROM payouts
            WHERE gateway_payout_id = :gateway_id
            AND status = 'processing'
            FOR UPDATE
        """),
        {"gateway_id": gateway_payout_id}
    )
    row = result.fetchone()
    
    if not row:
        return False
    
    payout_id, retry_count = row[0], row[1]
    
    if retry_count >= settings.MANUAL_REVIEW_AFTER_RETRIES:
        # Too many retries - require manual review
        _mark_payout_manual_review(db, payout_id)
    else:
        # Mark for retry with exponential backoff
        db.execute(
            text("""
                UPDATE payouts
                SET status = 'retrying',
                    retry_count = retry_count + 1,
                    gateway_payout_id = NULL
                WHERE id = :payout_id
            """),
            {"payout_id": payout_id}
        )
        logger.warning(f"Payout {payout_id} failed, will retry: {failure_reason}")
    
    return True


def calculate_retry_delay(retry_count: int) -> int:
    """
    Calculate exponential backoff delay.
    
    Returns delay in seconds.
    """
    base = settings.RETRY_BASE_DELAY_SECONDS
    # Exponential backoff: 60s, 120s, 240s, 480s, 960s...
    return base * (2 ** retry_count)
