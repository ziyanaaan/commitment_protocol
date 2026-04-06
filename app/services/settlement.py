from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.models.delivery_evidence import DeliveryEvidence
from app.models.settlement import Settlement
from app.services.decay import calculate_time_decay_payout
from app.core.logging import log
from app.services.razorpay_client import client
from app.models.payment import Payment



def settle_commitment(db: Session, commitment_id: int) -> Settlement:
    """
    Settle a commitment - calculate payout/refund based on delivery timing.
    This is idempotent - if settlement already exists, returns it.
    """
    print(">>> settle_commitment START", commitment_id)
    
    # Check if settlement already exists (idempotent)
    existing_settlement = (
        db.query(Settlement)
        .filter(Settlement.commitment_id == commitment_id)
        .first()
    )
    if existing_settlement:
        print(">>> Settlement already exists, returning it")
        return existing_settlement
    
    commitment = (
        db.query(Commitment)
        .filter(Commitment.id == commitment_id)
        .one_or_none()
    )
    print(">>> commitment:", commitment, commitment.status if commitment else None)

    if not commitment:
        raise ValueError("Commitment not found")

    if commitment.status not in {"delivered", "expired"}:
        raise ValueError(
            f"Cannot settle commitment in status {commitment.status}"
        )

    delivery = (
        db.query(Delivery)
        .filter(Delivery.commitment_id == commitment.id)
        .one_or_none()
    )
    print(">>> delivery:", delivery)

    # =====================================================================
    # EVIDENCE VALIDATION CHECK (NEW)
    # Settlement requires at least 1 validated evidence
    # =====================================================================
    if delivery:
        validated_evidence_count = (
            db.query(DeliveryEvidence)
            .filter(
                DeliveryEvidence.delivery_id == delivery.id,
                DeliveryEvidence.validated == True
            )
            .count()
        )
        
        if validated_evidence_count == 0:
            log.warning(
                "settlement: blocked due to missing validated evidence",
                extra={"commitment_id": commitment_id, "delivery_id": delivery.id}
            )
            raise ValueError(
                "Settlement blocked: no validated evidence found. "
                "At least 1 validated evidence is required."
            )
        
        print(f">>> Validated evidence count: {validated_evidence_count}")
    # =====================================================================

    delivered_at = delivery.submitted_at if delivery else None


    result = calculate_time_decay_payout(
        amount=Decimal(commitment.amount),
        deadline=commitment.deadline,
        delivered_at=delivered_at,
        decay_curve=commitment.decay_curve,
    )

    print(">>> calculating payout:", result)

    settlement = Settlement(
        commitment_id=commitment.id,
        delay_minutes=result["delay_minutes"] or 0,
        payout_amount=result["payout"],
        refund_amount=result["refund"],
        decay_applied=commitment.decay_curve,
    )

    commitment.status = "settled"

    try:
        print(">>> inserting settlement")
        db.add(settlement)
        db.add(commitment)
        db.commit()
        db.refresh(settlement)
        
        log.info(
            "commitment %s settled: payout=%s refund=%s",
            commitment.id,
            settlement.payout_amount,
            settlement.refund_amount,
        )
        
        # Try to process refund via Razorpay (optional, don't fail if this fails)
        try:
            payment = (
                db.query(Payment)
                .filter(Payment.commitment_id == commitment.id)
                .one_or_none()
            )
            
            if payment and payment.status == "paid" and settlement.refund_amount > 0:
                print(f">>> Processing refund of {settlement.refund_amount}")
                client.payment.refund(
                    payment.payment_id,
                    {"amount": int(settlement.refund_amount * 100)}
                )
                payment.status = "refunded"
                db.add(payment)
                db.commit()
                print(">>> Refund processed successfully")
            elif payment:
                print(f">>> No refund needed or payment status is {payment.status}")
        except Exception as refund_error:
            print(f">>> Refund failed (non-critical): {refund_error}")
            # Don't fail the settlement if refund fails - settlement is already saved
        
        print(">>> returning settlement", settlement)
        return settlement

    except IntegrityError:
        db.rollback()
        # Settlement already exists → return it
        print(">>> IntegrityError - settlement already exists")
        return (
            db.query(Settlement)
            .filter(Settlement.commitment_id == commitment.id)
            .order_by(Settlement.id.desc())
            .first()
        )
