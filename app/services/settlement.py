from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.models.settlement import Settlement
from app.services.decay import calculate_time_decay_payout
from app.core.logging import log
from app.services.razorpay_client import client
from app.models.payment import Payment





DEFAULT_DECAY_CURVE = [
    (0, 100),
    (60, 85),
    (180, 60),
    (360, 30),
]


def settle_commitment(db: Session, commitment_id: int) -> Settlement:
    print(">>> settle_commitment START", commitment_id)
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


    delivered_at = delivery.submitted_at if delivery else None

    result = calculate_time_decay_payout(
        amount=Decimal(commitment.amount),
        deadline=commitment.deadline,
        delivered_at=delivered_at,
        decay_curve=DEFAULT_DECAY_CURVE,
    )

    print(">>> calculating payout")

    settlement = Settlement(
        commitment_id=commitment.id,
        delay_minutes=result["delay_minutes"] or 0,
        payout_amount=result["payout"],
        refund_amount=result["refund"],
        decay_applied=DEFAULT_DECAY_CURVE,
    )
    

    commitment.status = "settled"

    try:
        print(">>> inserting settlement")

        db.add(settlement)
        db.add(commitment)
        db.commit()
        log.info(
            "commitment %s settled: payout=%s refund=%s",
            commitment.id,
            settlement.payout_amount,
            settlement.refund_amount,
        )
        payment = (
            db.query(Payment)
            .filter(Payment.commitment_id == commitment.id)
            .one_or_none()
        )
        if not payment or payment.status != "paid":
            raise ValueError("Cannot settle commitment with unpaid payment")

        #Refund unused amount only
        if settlement.refund_amount > 0:
            client.payment.refund(
                payment.payment_id,
                {
                    "amount": int(settlement.refund_amount * 100)
                }
            )
        
        payment.status = "refunded"
        db.add(payment)
        db.commit()
        db.refresh(settlement)
        print(">>> returning settlement", settlement)

        return settlement
        print(">>> END OF FUNCTION — NO RETURN HIT")


    except IntegrityError:
        db.rollback()
        # Settlement already exists → return it
        return (
            db.query(Settlement)
            .filter(Settlement.commitment_id == commitment.id)
            .order_by(Settlement.id.desc())
            .first()
        )
