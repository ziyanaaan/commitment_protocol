"""
Daily Financial Reconciliation Service.

Compares internal ledger totals with gateway data to detect financial drift.

CRITICAL RULES:
- Never auto-correct balances
- Never mutate ledger
- Detection only - no corrections
- Log all findings for audit

This job should run once per day.
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.financial.razorpay_client import get_payout, APIResponse


logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    """Result of a reconciliation run."""
    run_date: datetime
    status: str  # 'balanced', 'mismatch', 'error'
    
    # Ledger totals (in paise)
    ledger_credits: int
    ledger_debits: int
    ledger_balance: int
    
    # Gateway totals (in paise)
    gateway_captured: int
    gateway_payouts: int
    gateway_refunds: int
    gateway_balance: int
    
    # Comparison
    difference: int
    difference_percent: float
    
    # Breakdown
    pending_payouts: int
    pending_refunds: int
    holds_total: int
    holds_released: int
    holds_refunded: int
    
    # Errors
    errors: List[str]


# ============================================================================
# Main Entry Point
# ============================================================================

def run_daily_reconciliation(
    db: Session,
    for_date: Optional[datetime] = None,
) -> ReconciliationResult:
    """
    Run daily financial reconciliation.
    
    Compares internal ledger with gateway data.
    
    Args:
        db: Database session
        for_date: Date to reconcile (defaults to yesterday)
    
    Returns:
        ReconciliationResult with all findings
    """
    if for_date is None:
        for_date = datetime.now(timezone.utc) - timedelta(days=1)
    
    logger.info(f"Starting reconciliation for {for_date.date()}")
    
    errors = []
    
    # Step 1: Compute ledger totals
    try:
        ledger_data = _compute_ledger_totals(db)
    except Exception as e:
        logger.error(f"Failed to compute ledger totals: {e}")
        errors.append(f"Ledger computation failed: {e}")
        ledger_data = {"credits": 0, "debits": 0, "balance": 0}
    
    # Step 2: Get hold summaries
    try:
        holds_data = _compute_holds_summary(db)
    except Exception as e:
        logger.error(f"Failed to compute holds summary: {e}")
        errors.append(f"Holds computation failed: {e}")
        holds_data = {"total": 0, "released": 0, "refunded": 0}
    
    # Step 3: Get pending payout/refund amounts
    try:
        pending_data = _compute_pending_amounts(db)
    except Exception as e:
        logger.error(f"Failed to compute pending amounts: {e}")
        errors.append(f"Pending amounts failed: {e}")
        pending_data = {"payouts": 0, "refunds": 0}
    
    # Step 4: Get gateway transaction summary
    try:
        gateway_data = _fetch_gateway_summary(db)
    except Exception as e:
        logger.error(f"Failed to fetch gateway data: {e}")
        errors.append(f"Gateway fetch failed: {e}")
        gateway_data = {"captured": 0, "payouts": 0, "refunds": 0, "balance": 0}
    
    # Step 5: Calculate expected balance
    # Expected: captured - payouts_completed - refunds_completed
    ledger_balance = ledger_data["balance"]
    gateway_balance = gateway_data["balance"]
    difference = ledger_balance - gateway_balance
    
    # Calculate percentage difference
    if gateway_balance != 0:
        difference_percent = abs(difference) / gateway_balance * 100
    else:
        difference_percent = 0.0 if difference == 0 else 100.0
    
    # Determine status
    # Allow small tolerance (0.01% or 100 paise) for floating point issues
    TOLERANCE_PAISE = 100
    TOLERANCE_PERCENT = 0.01
    
    if abs(difference) <= TOLERANCE_PAISE or difference_percent <= TOLERANCE_PERCENT:
        status = "balanced"
        logger.info(f"Reconciliation BALANCED: ledger={ledger_balance}, gateway={gateway_balance}")
    else:
        status = "mismatch"
        logger.critical(
            f"RECONCILIATION MISMATCH DETECTED! "
            f"Ledger: {ledger_balance}, Gateway: {gateway_balance}, "
            f"Difference: {difference} ({difference_percent:.2f}%)"
        )
    
    if errors:
        status = "error"
    
    # Build result
    result = ReconciliationResult(
        run_date=datetime.now(timezone.utc),
        status=status,
        ledger_credits=ledger_data["credits"],
        ledger_debits=ledger_data["debits"],
        ledger_balance=ledger_balance,
        gateway_captured=gateway_data["captured"],
        gateway_payouts=gateway_data["payouts"],
        gateway_refunds=gateway_data["refunds"],
        gateway_balance=gateway_balance,
        difference=difference,
        difference_percent=difference_percent,
        pending_payouts=pending_data["payouts"],
        pending_refunds=pending_data["refunds"],
        holds_total=holds_data["total"],
        holds_released=holds_data["released"],
        holds_refunded=holds_data["refunded"],
        errors=errors,
    )
    
    # Step 6: Store reconciliation record
    _store_reconciliation_record(db, result)
    
    return result


# ============================================================================
# Ledger Computation
# ============================================================================

def _compute_ledger_totals(db: Session) -> Dict[str, int]:
    """
    Compute total credits and debits from ledger.
    
    Returns dict with credits, debits, balance (all in paise).
    """
    result = db.execute(
        text("""
            SELECT 
                COALESCE(SUM(CASE WHEN direction = 'credit' THEN amount ELSE 0 END), 0) as credits,
                COALESCE(SUM(CASE WHEN direction = 'debit' THEN amount ELSE 0 END), 0) as debits
            FROM ledger_entries
        """)
    )
    row = result.fetchone()
    
    credits = int(row[0]) if row else 0
    debits = int(row[1]) if row else 0
    
    return {
        "credits": credits,
        "debits": debits,
        "balance": credits - debits,
    }


def _compute_holds_summary(db: Session) -> Dict[str, int]:
    """
    Compute hold totals.
    
    Returns dict with total, released, refunded amounts.
    """
    result = db.execute(
        text("""
            SELECT 
                COALESCE(SUM(total_amount), 0) as total,
                COALESCE(SUM(released_amount), 0) as released,
                COALESCE(SUM(refunded_amount), 0) as refunded
            FROM holds
        """)
    )
    row = result.fetchone()
    
    return {
        "total": int(row[0]) if row else 0,
        "released": int(row[1]) if row else 0,
        "refunded": int(row[2]) if row else 0,
    }


def _compute_pending_amounts(db: Session) -> Dict[str, int]:
    """
    Compute pending payout and refund amounts.
    
    Returns amounts that are queued but not yet completed.
    """
    # Pending payouts
    payout_result = db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM payouts
            WHERE status IN ('queued', 'processing', 'retrying')
        """)
    )
    pending_payouts = int(payout_result.scalar() or 0)
    
    # Pending refunds
    refund_result = db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM refunds
            WHERE status IN ('created', 'pending_gateway')
        """)
    )
    pending_refunds = int(refund_result.scalar() or 0)
    
    return {
        "payouts": pending_payouts,
        "refunds": pending_refunds,
    }


# ============================================================================
# Gateway Data Fetch
# ============================================================================

def _fetch_gateway_summary(db: Session) -> Dict[str, int]:
    """
    Fetch transaction summary from gateway.
    
    For now, we calculate from our own records of gateway responses.
    In production, this would call Razorpay APIs for verification.
    
    Returns dict with captured, payouts, refunds, balance.
    """
    # Sum of captured payments (from our records)
    captured_result = db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM payments
            WHERE status = 'captured'
        """)
    )
    # Convert from rupees (Numeric) to paise
    captured_rupees = captured_result.scalar() or 0
    captured = int(Decimal(str(captured_rupees)) * 100)
    
    # Completed payouts
    payouts_result = db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM payouts
            WHERE status = 'completed'
        """)
    )
    payouts = int(payouts_result.scalar() or 0)
    
    # Completed refunds
    refunds_result = db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM refunds
            WHERE status = 'processed'
        """)
    )
    refunds = int(refunds_result.scalar() or 0)
    
    # Gateway balance = captured - payouts - refunds
    balance = captured - payouts - refunds
    
    return {
        "captured": captured,
        "payouts": payouts,
        "refunds": refunds,
        "balance": balance,
    }


# ============================================================================
# Record Storage
# ============================================================================

def _store_reconciliation_record(
    db: Session,
    result: ReconciliationResult,
) -> None:
    """
    Store reconciliation result for audit trail.
    
    Uses balance_snapshots table.
    """
    try:
        db.execute(
            text("""
                INSERT INTO balance_snapshots (
                    snapshot_date,
                    ledger_balance,
                    gateway_balance,
                    holds_balance,
                    pending_payouts,
                    pending_refunds,
                    reconciled,
                    discrepancy_amount,
                    notes
                ) VALUES (
                    :snapshot_date,
                    :ledger_balance,
                    :gateway_balance,
                    :holds_balance,
                    :pending_payouts,
                    :pending_refunds,
                    :reconciled,
                    :discrepancy_amount,
                    :notes
                )
            """),
            {
                "snapshot_date": result.run_date.date(),
                "ledger_balance": result.ledger_balance,
                "gateway_balance": result.gateway_balance,
                "holds_balance": result.holds_total - result.holds_released - result.holds_refunded,
                "pending_payouts": result.pending_payouts,
                "pending_refunds": result.pending_refunds,
                "reconciled": result.status == "balanced",
                "discrepancy_amount": result.difference if result.status == "mismatch" else 0,
                "notes": "; ".join(result.errors) if result.errors else None,
            }
        )
        db.commit()
        logger.info(f"Stored reconciliation record for {result.run_date.date()}")
    except Exception as e:
        logger.error(f"Failed to store reconciliation record: {e}")
        db.rollback()


# ============================================================================
# Query Functions
# ============================================================================

def get_recent_reconciliations(
    db: Session,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """
    Get recent reconciliation records.
    
    For admin dashboard display.
    """
    result = db.execute(
        text("""
            SELECT 
                snapshot_date,
                ledger_balance,
                gateway_balance,
                holds_balance,
                pending_payouts,
                pending_refunds,
                reconciled,
                discrepancy_amount,
                notes,
                created_at
            FROM balance_snapshots
            ORDER BY snapshot_date DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    
    return [dict(row._mapping) for row in result.fetchall()]


def get_unreconciled_days(
    db: Session,
    days_back: int = 30,
) -> List[Dict[str, Any]]:
    """
    Get days with reconciliation issues.
    
    For alerts display.
    """
    result = db.execute(
        text("""
            SELECT 
                snapshot_date,
                discrepancy_amount,
                notes
            FROM balance_snapshots
            WHERE reconciled = false
            AND snapshot_date >= :start_date
            ORDER BY snapshot_date DESC
        """),
        {"start_date": datetime.now(timezone.utc).date() - timedelta(days=days_back)}
    )
    
    return [dict(row._mapping) for row in result.fetchall()]
