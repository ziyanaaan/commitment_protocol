from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.schemas.delivery import DeliveryCreate


def deliver_commitment(
    db: Session,
    commitment_id: int,
    payload: DeliveryCreate,
) -> Delivery:

    print(">>> deliver_commitment CALLED")

    commitment = (
        db.query(Commitment)
        .filter(Commitment.id == commitment_id)
        .one_or_none()
    )
    if not commitment:
        raise ValueError("Commitment not found")

    if commitment.status != "locked":
        raise ValueError(f"Cannot deliver in status {commitment.status}")

    existing = (
        db.query(Delivery)
        .filter(Delivery.commitment_id == commitment_id)
        .one_or_none()
    )
    if existing:
        return existing

    delivery = Delivery(
        commitment_id=commitment_id,
        artifact_type=payload.artifact_type,
        artifact_reference=payload.artifact_reference,
    )

    commitment.status = "delivered"

    print(">>> inserting delivery row")
    db.add(delivery)
    db.add(commitment)
    db.commit()
    db.refresh(delivery)

    print(">>> delivery committed")

    return delivery
