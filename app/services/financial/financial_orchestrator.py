"""
Financial Orchestrator - Settlement to Financial Execution Bridge.

This module coordinates the financial actions after a commitment is settled:
1. Lock settlement row
2. Check financial_processed flag (idempotency)
3. Lock hold row
4. Create payout/refund records
5. Update hold amounts
6. Write ledger entries
7. Mark settlement as financially processed

CRITICAL:
- Does NOT call external gateways
- Only queues financial actions
- Uses row-level locking
- Fully transactional
- Idempotent via financial_processed flag
"""

from typing import Optional, Tuple, Any
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.settlement import Settlement
from app.models.financial.hold import Hold
from app.models.financial.payout import Payout
from app.models.financial.refund import Refund


# ============================================================================
# Exceptions
# ============================================================================

class OrchestrationError(Exception):
    """Base exception for orchestration errors."""
    pass


class SettlementNotFound(OrchestrationError):
    """Settlement doesn't exist."""
    pass


class SettlementAlreadyProcessed(OrchestrationError):
    """Settlement was already financially processed."""
    pass


class HoldNotFound(OrchestrationError):
    """Hold doesn't exist for this commitment."""
    pass


class InsufficientHoldBalance(OrchestrationError):
    """Hold doesn't have enough balance."""
    pass


# ============================================================================
# Main Entry Point
# ============================================================================

def execute(
    db: Session,
    commitment_id: int,
) -> dict:
    """
    Execute financial actions for a settled commitment.
    
    This is THE main entry point for settlement → financial bridge.
    
    CRITICAL:
    - All operations are transactional
    - Uses SELECT FOR UPDATE to prevent race conditions
    - Idempotent via financial_processed flag
    - Does NOT call external gateways
    
    Args:
        db: Database session (caller is responsible for commit)
        commitment_id: The commitment ID (Integer)
    
    Returns:
        Dict with execution results:
        {
            "status": "processed" | "already_processed" | "no_action",
            "payout_id": int | None,
            "refund_id": int | None,
            "payout_amount": int,
            "refund_amount": int,
        }
    
    Raises:
        SettlementNotFound: If settlement doesn't exist
        HoldNotFound: If hold doesn't exist
        InsufficientHoldBalance: If hold balance is insufficient
    """
    # Step 1: Lock and fetch settlement
    settlement = _lock_settlement(db, commitment_id)
    
    if not settlement:
        raise SettlementNotFound(f"Settlement not found for commitment {commitment_id}")
    
    # Step 2: Check idempotency - if already processed, exit immediately
    if _is_financially_processed(db, settlement["id"]):
        return {
            "status": "already_processed",
            "payout_id": None,
            "refund_id": None,
            "payout_amount": 0,
            "refund_amount": 0,
        }
    
    # Step 3: Lock and fetch hold
    hold = _lock_hold(db, commitment_id)
    
    if not hold:
        raise HoldNotFound(f"Hold not found for commitment {commitment_id}")
    
    # Step 4: Read settlement amounts (convert Decimal to int paise)
    payout_amount = _to_paise(settlement["payout_amount"])
    refund_amount = _to_paise(settlement["refund_amount"])
    
    # Step 5: Verify hold has sufficient balance
    available = hold["total_amount"] - hold["released_amount"] - hold["refunded_amount"]
    required = payout_amount + refund_amount
    
    if required > available:
        raise InsufficientHoldBalance(
            f"Hold {hold['id']} has {available} available, but {required} required"
        )
    
    # If nothing to do, mark as processed and exit
    if payout_amount == 0 and refund_amount == 0:
        _mark_financially_processed(db, settlement["id"])
        return {
            "status": "no_action",
            "payout_id": None,
            "refund_id": None,
            "payout_amount": 0,
            "refund_amount": 0,
        }
    
    payout_id = None
    refund_id = None
    
    # Step 6: Create payout if needed
    if payout_amount > 0:
        payout_id = _create_payout(
            db,
            commitment_id=commitment_id,
            amount=payout_amount,
        )
        
        # Update hold released_amount
        _update_hold_released(db, hold["id"], payout_amount)
        
        # Write ledger entry
        _write_ledger_entry(
            db,
            entry_type="payout_debit",
            amount=payout_amount,
            direction="debit",
            reference_table="payouts",
            reference_id=payout_id,
            commitment_id=commitment_id,
        )
    
    # Step 7: Create refund if needed
    if refund_amount > 0:
        refund_id = _create_refund(
            db,
            commitment_id=commitment_id,
            payment_id=hold["payment_id"],
            amount=refund_amount,
        )
        
        # Update hold refunded_amount
        _update_hold_refunded(db, hold["id"], refund_amount)
        
        # Write ledger entry
        _write_ledger_entry(
            db,
            entry_type="refund_debit",
            amount=refund_amount,
            direction="debit",
            reference_table="refunds",
            reference_id=refund_id,
            commitment_id=commitment_id,
        )
    
    # Step 8: Update hold status
    _update_hold_status(db, hold["id"])
    
    # Step 9: Mark settlement as financially processed
    _mark_financially_processed(db, settlement["id"])
    
    db.flush()
    
    return {
        "status": "processed",
        "payout_id": payout_id,
        "refund_id": refund_id,
        "payout_amount": payout_amount,
        "refund_amount": refund_amount,
    }


# ============================================================================
# Internal Functions
# ============================================================================

def _to_paise(amount: Decimal) -> int:
    """Convert Decimal rupees to integer paise."""
    if amount is None:
        return 0
    return int(amount * 100)


def _lock_settlement(db: Session, commitment_id: int) -> Optional[dict]:
    """Lock and fetch settlement row."""
    result = db.execute(
        text("""
            SELECT id, commitment_id, payout_amount, refund_amount
            FROM settlements
            WHERE commitment_id = :commitment_id
            FOR UPDATE
        """),
        {"commitment_id": commitment_id}
    )
    row = result.fetchone()
    
    if not row:
        return None
    
    return {
        "id": row[0],
        "commitment_id": row[1],
        "payout_amount": row[2],
        "refund_amount": row[3],
    }


def _is_financially_processed(db: Session, settlement_id: int) -> bool:
    """Check if settlement is already financially processed."""
    # Check if financial_processed column exists and is true
    # If column doesn't exist, we use a payout/refund exists check as fallback
    try:
        result = db.execute(
            text("""
                SELECT financial_processed
                FROM settlements
                WHERE id = :settlement_id
            """),
            {"settlement_id": settlement_id}
        )
        row = result.fetchone()
        return row[0] if row else False
    except Exception:
        # Column doesn't exist - check if payout exists as fallback
        result = db.execute(
            text("""
                SELECT COUNT(*) FROM payouts
                WHERE commitment_id = (
                    SELECT commitment_id FROM settlements WHERE id = :settlement_id
                )
            """),
            {"settlement_id": settlement_id}
        )
        return result.scalar() > 0


def _mark_financially_processed(db: Session, settlement_id: int) -> None:
    """Mark settlement as financially processed."""
    try:
        db.execute(
            text("""
                UPDATE settlements
                SET financial_processed = true
                WHERE id = :settlement_id
            """),
            {"settlement_id": settlement_id}
        )
    except Exception:
        # Column doesn't exist - skip (payout existence serves as check)
        pass


def _lock_hold(db: Session, commitment_id: int) -> Optional[dict]:
    """Lock and fetch hold row."""
    result = db.execute(
        text("""
            SELECT id, payment_id, commitment_id, total_amount, 
                   released_amount, refunded_amount, status
            FROM holds
            WHERE commitment_id = :commitment_id
            FOR UPDATE
        """),
        {"commitment_id": commitment_id}
    )
    row = result.fetchone()
    
    if not row:
        return None
    
    return {
        "id": row[0],
        "payment_id": row[1],
        "commitment_id": row[2],
        "total_amount": row[3],
        "released_amount": row[4],
        "refunded_amount": row[5],
        "status": row[6],
    }


def _create_payout(
    db: Session,
    commitment_id: int,
    amount: int,
) -> int:
    """Create a queued payout record."""
    idempotency_key = f"payout_{commitment_id}"
    
    # Check if already exists (idempotency)
    result = db.execute(
        text("""
            SELECT id FROM payouts
            WHERE idempotency_key = :key
        """),
        {"key": idempotency_key}
    )
    existing = result.fetchone()
    if existing:
        return existing[0]
    
    # Insert new payout
    result = db.execute(
        text("""
            INSERT INTO payouts (
                commitment_id, user_id, amount, currency, status,
                idempotency_key, retry_count, created_at
            )
            SELECT 
                :commitment_id,
                c.freelancer_id,
                :amount,
                'INR',
                'queued',
                :idempotency_key,
                0,
                NOW()
            FROM commitments c
            WHERE c.id = :commitment_id
            RETURNING id
        """),
        {
            "commitment_id": commitment_id,
            "amount": amount,
            "idempotency_key": idempotency_key,
        }
    )
    return result.fetchone()[0]


def _create_refund(
    db: Session,
    commitment_id: int,
    payment_id: Any,
    amount: int,
) -> int:
    """Create a refund record."""
    # Check if already exists
    result = db.execute(
        text("""
            SELECT id FROM refunds
            WHERE commitment_id = :commitment_id
            AND amount = :amount
            AND status != 'failed'
        """),
        {"commitment_id": commitment_id, "amount": amount}
    )
    existing = result.fetchone()
    if existing:
        return existing[0]
    
    # Insert new refund
    result = db.execute(
        text("""
            INSERT INTO refunds (
                payment_id, commitment_id, amount, currency, status,
                reason, created_at
            )
            VALUES (
                :payment_id, :commitment_id, :amount, 'INR', 'created',
                'Settlement refund', NOW()
            )
            RETURNING id
        """),
        {
            "payment_id": payment_id,
            "commitment_id": commitment_id,
            "amount": amount,
        }
    )
    return result.fetchone()[0]


def _update_hold_released(db: Session, hold_id: Any, amount: int) -> None:
    """Update hold released_amount."""
    db.execute(
        text("""
            UPDATE holds
            SET released_amount = released_amount + :amount
            WHERE id = :hold_id
        """),
        {"hold_id": hold_id, "amount": amount}
    )


def _update_hold_refunded(db: Session, hold_id: Any, amount: int) -> None:
    """Update hold refunded_amount."""
    db.execute(
        text("""
            UPDATE holds
            SET refunded_amount = refunded_amount + :amount
            WHERE id = :hold_id
        """),
        {"hold_id": hold_id, "amount": amount}
    )


def _update_hold_status(db: Session, hold_id: Any) -> None:
    """Update hold status based on amounts."""
    db.execute(
        text("""
            UPDATE holds
            SET status = CASE
                WHEN released_amount + refunded_amount >= total_amount THEN 'consumed'
                WHEN released_amount > 0 OR refunded_amount > 0 THEN 'partially_released'
                ELSE status
            END
            WHERE id = :hold_id
        """),
        {"hold_id": hold_id}
    )


def _write_ledger_entry(
    db: Session,
    entry_type: str,
    amount: int,
    direction: str,
    reference_table: str,
    reference_id: Any,
    commitment_id: int,
    user_id: Optional[int] = None,
) -> None:
    """Write a ledger entry using raw SQL."""
    db.execute(
        text("""
            INSERT INTO ledger_entries (
                user_id, commitment_id, entry_type, amount, currency,
                direction, reference_table, reference_id, created_at
            )
            VALUES (
                :user_id, :commitment_id, :entry_type, :amount, 'INR',
                :direction, :reference_table, :reference_id, NOW()
            )
        """),
        {
            "user_id": user_id,
            "commitment_id": commitment_id,
            "entry_type": entry_type,
            "amount": amount,
            "direction": direction,
            "reference_table": reference_table,
            "reference_id": reference_id,
        }
    )


# ============================================================================
# Query Functions
# ============================================================================

def get_pending_payouts(db: Session, limit: int = 100) -> list:
    """Get payouts ready for processing."""
    result = db.execute(
        text("""
            SELECT id, commitment_id, user_id, amount, status, retry_count
            FROM payouts
            WHERE status IN ('queued', 'retrying')
            ORDER BY created_at
            LIMIT :limit
        """),
        {"limit": limit}
    )
    return [dict(row._mapping) for row in result.fetchall()]


def get_pending_refunds(db: Session, limit: int = 100) -> list:
    """Get refunds ready for processing."""
    result = db.execute(
        text("""
            SELECT id, payment_id, commitment_id, amount, status
            FROM refunds
            WHERE status = 'created'
            ORDER BY created_at
            LIMIT :limit
        """),
        {"limit": limit}
    )
    return [dict(row._mapping) for row in result.fetchall()]
