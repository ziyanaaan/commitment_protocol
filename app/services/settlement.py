from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.models.settlement import Settlement
from app.services.decay import calculate_time_decay_payout
from app.core.logging import log



DEFAULT_DECAY_CURVE = [
    (0, 100),
    (60, 85),
    (180, 60),
    (360, 30),
]


def settle_commitment(db: Session, commitment_id: int) -> Settlement:
    commitment = (
        db.query(Commitment)
        .filter(Commitment.id == commitment_id)
        .one_or_none()
    )

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

    delivered_at = delivery.submitted_at if delivery else None

    result = calculate_time_decay_payout(
        amount=Decimal(commitment.amount),
        deadline=commitment.deadline,
        delivered_at=delivered_at,
        decay_curve=DEFAULT_DECAY_CURVE,
    )

    settlement = Settlement(
        commitment_id=commitment.id,
        delay_minutes=result["delay_minutes"] or 0,
        payout_amount=result["payout"],
        refund_amount=result["refund"],
    )

    commitment.status = "settled"

    try:
        db.add(settlement)
        db.add(commitment)
        db.commit()
        log.info(
            "commitment %s settled: payout=%s refund=%s",
            commitment.id,
            settlement.payout_amount,
            settlement.refund_amount,
        )

        return settlement

    except IntegrityError:
        db.rollback()
        # Settlement already exists → return it
        return (
            db.query(Settlement)
            .filter(Settlement.commitment_id == commitment.id)
            .one()
        )
