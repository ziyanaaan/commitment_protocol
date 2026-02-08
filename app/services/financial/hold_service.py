"""
Hold Service - Escrow management for committed payments.

Manages the lifecycle of payment holds:
1. create_hold - Create a new hold when payment is captured
2. release_hold - Release funds to freelancer (payout)
3. refund_hold - Refund funds to client
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.financial.hold import Hold
from app.services.financial.ledger_service import (
    create_ledger_entry,
    LedgerEntryType,
    LedgerDirection,
)


class HoldError(Exception):
    """Base exception for hold operations."""
    pass


class InsufficientHoldBalance(HoldError):
    """Raised when trying to release/refund more than available."""
    pass


class HoldNotFound(HoldError):
    """Raised when hold doesn't exist."""
    pass


class HoldNotActive(HoldError):
    """Raised when hold is not in active state."""
    pass


def create_hold(
    db: Session,
    *,
    payment_id: UUID,
    commitment_id: UUID,
    amount: int,
    currency: str = "INR",
) -> Hold:
    """
    Create a new escrow hold for a payment.
    
    This is called when a payment is captured and funds are held in escrow.
    
    Args:
        db: Database session
        payment_id: The payment ID
        commitment_id: The commitment ID
        amount: Amount in smallest currency unit (MUST be positive)
        currency: Currency code
    
    Returns:
        Created Hold record
    
    Raises:
        ValueError: If amount is not positive
    """
    if amount <= 0:
        raise ValueError(f"Hold amount must be positive, got {amount}")
    
    # Create the hold record
    hold = Hold(
        payment_id=payment_id,
        commitment_id=commitment_id,
        total_amount=amount,
        released_amount=0,
        refunded_amount=0,
        status="active",
    )
    db.add(hold)
    db.flush()  # Get the hold ID
    
    # Record ledger entries for the hold
    # 1. Credit: Money received from payment
    create_ledger_entry(
        db,
        entry_type=LedgerEntryType.PAYMENT_CREDIT,
        amount=amount,
        direction=LedgerDirection.CREDIT,
        reference_table="payments",
        reference_id=payment_id,
        commitment_id=commitment_id,
        currency=currency,
    )
    
    # 2. Debit: Money moved to hold
    create_ledger_entry(
        db,
        entry_type=LedgerEntryType.HOLD_DEBIT,
        amount=amount,
        direction=LedgerDirection.DEBIT,
        reference_table="holds",
        reference_id=hold.id,
        commitment_id=commitment_id,
        currency=currency,
    )
    
    return hold


def release_hold(
    db: Session,
    *,
    hold_id: UUID,
    amount: int,
    user_id: UUID,
) -> Hold:
    """
    Release funds from hold (for freelancer payout).
    
    Uses SELECT FOR UPDATE to prevent race conditions.
    
    Args:
        db: Database session
        hold_id: The hold ID
        amount: Amount to release
        user_id: The freelancer user ID
    
    Returns:
        Updated Hold record
    
    Raises:
        HoldNotFound: If hold doesn't exist
        HoldNotActive: If hold is not in releasable state
        InsufficientHoldBalance: If amount exceeds available
    """
    if amount <= 0:
        raise ValueError(f"Release amount must be positive, got {amount}")
    
    # Lock the hold row for update
    hold = (
        db.query(Hold)
        .filter(Hold.id == hold_id)
        .with_for_update()
        .first()
    )
    
    if not hold:
        raise HoldNotFound(f"Hold {hold_id} not found")
    
    if hold.status not in ("active", "partially_released"):
        raise HoldNotActive(f"Hold {hold_id} is {hold.status}, cannot release")
    
    available = hold.total_amount - hold.released_amount - hold.refunded_amount
    if amount > available:
        raise InsufficientHoldBalance(
            f"Cannot release {amount}, only {available} available"
        )
    
    # Update hold
    hold.released_amount += amount
    
    # Update status
    if hold.released_amount + hold.refunded_amount >= hold.total_amount:
        hold.status = "released"
    else:
        hold.status = "partially_released"
    
    # Record ledger entry
    create_ledger_entry(
        db,
        entry_type=LedgerEntryType.HOLD_RELEASE,
        amount=amount,
        direction=LedgerDirection.CREDIT,
        reference_table="holds",
        reference_id=hold.id,
        commitment_id=hold.commitment_id,
        user_id=user_id,
    )
    
    db.flush()
    return hold


def refund_hold(
    db: Session,
    *,
    hold_id: UUID,
    amount: int,
    user_id: UUID,
    reason: Optional[str] = None,
) -> Hold:
    """
    Refund funds from hold (back to client).
    
    Uses SELECT FOR UPDATE to prevent race conditions.
    
    Args:
        db: Database session
        hold_id: The hold ID
        amount: Amount to refund
        user_id: The client user ID
        reason: Optional refund reason
    
    Returns:
        Updated Hold record
    
    Raises:
        HoldNotFound: If hold doesn't exist
        HoldNotActive: If hold is not in refundable state
        InsufficientHoldBalance: If amount exceeds available
    """
    if amount <= 0:
        raise ValueError(f"Refund amount must be positive, got {amount}")
    
    # Lock the hold row for update
    hold = (
        db.query(Hold)
        .filter(Hold.id == hold_id)
        .with_for_update()
        .first()
    )
    
    if not hold:
        raise HoldNotFound(f"Hold {hold_id} not found")
    
    if hold.status not in ("active", "partially_released"):
        raise HoldNotActive(f"Hold {hold_id} is {hold.status}, cannot refund")
    
    available = hold.total_amount - hold.released_amount - hold.refunded_amount
    if amount > available:
        raise InsufficientHoldBalance(
            f"Cannot refund {amount}, only {available} available"
        )
    
    # Update hold
    hold.refunded_amount += amount
    
    # Update status
    if hold.released_amount + hold.refunded_amount >= hold.total_amount:
        hold.status = "refunded"
    
    # Record ledger entry
    create_ledger_entry(
        db,
        entry_type=LedgerEntryType.REFUND_DEBIT,
        amount=amount,
        direction=LedgerDirection.DEBIT,
        reference_table="holds",
        reference_id=hold.id,
        commitment_id=hold.commitment_id,
        user_id=user_id,
    )
    
    db.flush()
    return hold


def get_hold_by_commitment(
    db: Session,
    commitment_id: UUID,
) -> Optional[Hold]:
    """Get the hold for a commitment."""
    return (
        db.query(Hold)
        .filter(Hold.commitment_id == commitment_id)
        .first()
    )


def get_hold_by_payment(
    db: Session,
    payment_id: UUID,
) -> Optional[Hold]:
    """Get the hold for a payment."""
    return (
        db.query(Hold)
        .filter(Hold.payment_id == payment_id)
        .first()
    )
