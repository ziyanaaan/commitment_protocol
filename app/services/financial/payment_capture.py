"""
Payment Capture Service.

Handles the capture of payments when gateway confirms successful capture.

CRITICAL RULES:
- All operations must be transactional
- Lock payment row before updating
- Idempotency: skip if already captured
- All ledger writes through ledger_service
"""

from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.financial.hold import Hold
from app.services.financial.ledger_service import (
    create_ledger_entry,
    LedgerEntryType,
    LedgerDirection,
)


class PaymentCaptureError(Exception):
    """Base exception for payment capture errors."""
    pass


class PaymentNotFound(PaymentCaptureError):
    """Payment doesn't exist."""
    pass


class PaymentAlreadyCaptured(PaymentCaptureError):
    """Payment was already captured."""
    pass


class HoldCreationFailed(PaymentCaptureError):
    """Hold creation failed."""
    pass


def process_payment_captured(
    db: Session,
    *,
    gateway_payment_id: str,
    captured_amount: int,
    currency: str = "INR",
    gateway_data: Optional[dict] = None,
) -> Tuple:
    """
    Process a payment.captured event from the gateway.
    
    This function:
    1. Finds and locks the payment row
    2. Ensures it's not already captured
    3. Creates ledger entry (payment_credit)
    4. Creates hold
    5. Creates ledger entry (hold_debit)
    6. Updates payment status
    
    CRITICAL: This must run inside a transaction.
    
    Args:
        db: Database session
        gateway_payment_id: Gateway's payment ID
        captured_amount: Amount captured in smallest currency unit
        currency: Currency code
        gateway_data: Optional gateway metadata
    
    Returns:
        Tuple of (payment, hold)
    
    Raises:
        PaymentNotFound: If payment doesn't exist
        PaymentAlreadyCaptured: If payment already captured
        HoldCreationFailed: If hold creation fails
    """
    # Import Payment model here to avoid circular imports
    from app.models.commitment import Commitment
    
    # Step 1: Find payment by gateway_payment_id
    # For now, we'll look up via the payment_intent_id in payments table
    # First, check if we can find a commitment with this payment
    
    # We need to find the payment record
    # The Payment model should have gateway_payment_id field
    # For now, we'll use a raw query approach
    
    result = db.execute(
        """
        SELECT id, commitment_id, amount, status, user_id
        FROM payments
        WHERE gateway_payment_id = :gateway_id
        FOR UPDATE
        """,
        {"gateway_id": gateway_payment_id}
    )
    payment_row = result.fetchone()
    
    if not payment_row:
        raise PaymentNotFound(f"Payment with gateway_id {gateway_payment_id} not found")
    
    payment_id = payment_row.id
    commitment_id = payment_row.commitment_id
    current_status = payment_row.status
    user_id = payment_row.user_id
    
    # Step 2: Idempotency check - skip if already captured
    if current_status == "captured":
        raise PaymentAlreadyCaptured(f"Payment {payment_id} already captured")
    
    # Step 3: Create ledger entry for payment credit
    create_ledger_entry(
        db,
        entry_type=LedgerEntryType.PAYMENT_CREDIT,
        amount=captured_amount,
        direction=LedgerDirection.CREDIT,
        reference_table="payments",
        reference_id=payment_id,
        commitment_id=commitment_id,
        user_id=user_id,
        currency=currency,
    )
    
    # Step 4: Create hold
    hold = Hold(
        payment_id=payment_id,
        commitment_id=commitment_id,
        total_amount=captured_amount,
        released_amount=0,
        refunded_amount=0,
        status="active",
    )
    db.add(hold)
    db.flush()  # Get hold ID
    
    # Step 5: Create ledger entry for hold debit
    create_ledger_entry(
        db,
        entry_type=LedgerEntryType.HOLD_DEBIT,
        amount=captured_amount,
        direction=LedgerDirection.DEBIT,
        reference_table="holds",
        reference_id=hold.id,
        commitment_id=commitment_id,
        currency=currency,
    )
    
    # Step 6: Update payment status
    db.execute(
        """
        UPDATE payments
        SET status = 'captured',
            captured_at = :now
        WHERE id = :payment_id
        """,
        {
            "payment_id": payment_id,
            "now": datetime.now(timezone.utc),
        }
    )
    
    # Also update commitment status if needed
    db.execute(
        """
        UPDATE commitments
        SET status = 'paid'
        WHERE id = :commitment_id
        AND status = 'funded'
        """,
        {"commitment_id": commitment_id}
    )
    
    db.flush()
    
    return payment_id, hold


def get_payment_by_gateway_id(
    db: Session,
    gateway_payment_id: str,
) -> Optional[dict]:
    """
    Get payment record by gateway payment ID.
    """
    result = db.execute(
        """
        SELECT id, commitment_id, amount, status, user_id, gateway_payment_id
        FROM payments
        WHERE gateway_payment_id = :gateway_id
        """,
        {"gateway_id": gateway_payment_id}
    )
    row = result.fetchone()
    
    if not row:
        return None
    
    return {
        "id": row.id,
        "commitment_id": row.commitment_id,
        "amount": row.amount,
        "status": row.status,
        "user_id": row.user_id,
        "gateway_payment_id": row.gateway_payment_id,
    }
