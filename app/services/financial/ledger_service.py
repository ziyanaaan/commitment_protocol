"""
Ledger Service - Append-only financial source of truth.

CRITICAL: This service is the ONLY way to record financial transactions.

Rules:
1. Ledger is APPEND-ONLY - never update or delete entries
2. All money movement MUST pass through this service
3. Amounts are ALWAYS positive - direction indicates credit/debit
4. All amounts in smallest currency unit (paise for INR)
"""

from typing import Optional
from uuid import UUID
from enum import Enum
from sqlalchemy.orm import Session

from app.models.financial.ledger_entry import FinancialLedgerEntry as LedgerEntry


class LedgerEntryType(str, Enum):
    """Valid ledger entry types."""
    PAYMENT_CREDIT = "payment_credit"      # Money received from client
    HOLD_DEBIT = "hold_debit"              # Money moved to escrow hold
    HOLD_RELEASE = "hold_release"          # Money released from hold
    PAYOUT_DEBIT = "payout_debit"          # Money paid to freelancer
    REFUND_DEBIT = "refund_debit"          # Money refunded to client
    FEE_DEBIT = "fee_debit"                # Platform fee
    ADJUSTMENT = "adjustment"              # Manual adjustment
    REVERSAL = "reversal"                  # Reversal of previous entry


class LedgerDirection(str, Enum):
    """Direction of money flow."""
    CREDIT = "credit"  # Money coming in
    DEBIT = "debit"    # Money going out


def create_ledger_entry(
    db: Session,
    *,
    entry_type: LedgerEntryType,
    amount: int,
    direction: LedgerDirection,
    reference_table: str,
    reference_id: UUID,
    user_id: Optional[UUID] = None,
    commitment_id: Optional[UUID] = None,
    currency: str = "INR",
) -> LedgerEntry:
    """
    Create an immutable ledger entry.
    
    CRITICAL: This function is the ONLY way to record financial transactions.
    
    Args:
        db: Database session
        entry_type: Type of ledger entry
        amount: Amount in smallest currency unit (MUST be positive)
        direction: Credit or debit
        reference_table: Name of the source table (e.g., 'payments', 'holds')
        reference_id: ID of the source record
        user_id: Optional user ID
        commitment_id: Optional commitment ID
        currency: Currency code (default: INR)
    
    Returns:
        Created LedgerEntry
    
    Raises:
        ValueError: If amount is not positive
    """
    # CRITICAL: Validate amount is positive
    if amount <= 0:
        raise ValueError(f"Ledger amount must be positive, got {amount}")
    
    # CRITICAL: Validate entry type
    if entry_type not in LedgerEntryType:
        raise ValueError(f"Invalid entry type: {entry_type}")
    
    # CRITICAL: Validate direction
    if direction not in LedgerDirection:
        raise ValueError(f"Invalid direction: {direction}")
    
    entry = LedgerEntry(
        user_id=user_id,
        commitment_id=commitment_id,
        entry_type=entry_type.value,
        amount=amount,
        currency=currency,
        direction=direction.value,
        reference_table=reference_table,
        reference_id=reference_id,
    )
    
    db.add(entry)
    db.flush()  # Get ID without committing
    
    return entry


def get_commitment_ledger_entries(
    db: Session,
    commitment_id: UUID,
) -> list[LedgerEntry]:
    """
    Get all ledger entries for a commitment.
    
    Args:
        db: Database session
        commitment_id: Commitment ID
    
    Returns:
        List of ledger entries, ordered by created_at
    """
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.commitment_id == commitment_id)
        .order_by(LedgerEntry.created_at)
        .all()
    )


def get_user_ledger_entries(
    db: Session,
    user_id: UUID,
    limit: int = 100,
) -> list[LedgerEntry]:
    """
    Get recent ledger entries for a user.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum entries to return
    
    Returns:
        List of ledger entries, ordered by created_at desc
    """
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.user_id == user_id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(limit)
        .all()
    )
