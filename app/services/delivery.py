from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.schemas.delivery import DeliveryCreate
from app.services.settlement import settle_commitment


def deliver_commitment(
    db: Session,
    commitment_id: int,
    payload: DeliveryCreate,
):
    """
    Deliver a commitment. This is idempotent:
    - If already delivered/settled, returns existing delivery
    - If locked, creates new delivery and auto-settles
    - Otherwise raises ValueError
    """
    print(">>> deliver_commitment CALLED for", commitment_id)

    # Use FOR UPDATE to lock the row and prevent race conditions
    commitment = (
        db.query(Commitment)
        .filter(Commitment.id == commitment_id)
        .with_for_update()
        .one_or_none()
    )
    if not commitment:
        raise ValueError("Commitment not found")

    print(f">>> Commitment status: {commitment.status}")

    # IDEMPOTENT: If already delivered or settled, return existing delivery
    if commitment.status in ("delivered", "settled"):
        existing = (
            db.query(Delivery)
            .filter(Delivery.commitment_id == commitment_id)
            .first()
        )
        if existing:
            print(">>> Already delivered/settled, returning existing delivery")
            return existing
        else:
            # Settled without delivery (e.g., expired) - still return success info
            raise ValueError(f"Commitment is already {commitment.status}")
    
    # IDEMPOTENT: If expired, cannot deliver anymore
    if commitment.status == "expired":
        raise ValueError("Cannot deliver - commitment has expired")
    
    # Only allow delivery if locked
    if commitment.status != "locked":
        raise ValueError(f"Cannot deliver in status '{commitment.status}'")

    # Double-check for existing delivery with lock held
    existing = (
        db.query(Delivery)
        .filter(Delivery.commitment_id == commitment_id)
        .first()
    )
    if existing:
        print(">>> Existing delivery found (race condition prevented), returning it")
        return existing

    # Create new delivery
    delivery = Delivery(
        commitment_id=commitment_id,
        artifact_type=payload.artifact_type,
        artifact_reference=payload.artifact_reference,
    )

    commitment.status = "delivered"

    print(">>> Inserting delivery row")
    db.add(delivery)
    db.add(commitment)
    
    try:
        db.commit()
        db.refresh(delivery)
    except IntegrityError:
        db.rollback()
        # Race condition: another request created the delivery
        existing = db.query(Delivery).filter(Delivery.commitment_id == commitment_id).first()
        if existing:
            print(">>> IntegrityError caught, returning existing delivery")
            return existing
        raise

    print(">>> Delivery committed, now settling")
    
    # Auto-settle after delivery
    try:
        settlement = settle_commitment(db, commitment_id)
        print(">>> Settlement complete")
        return {
            "delivery": delivery,
            "settlement": settlement
        }
    except Exception as e:
        print(f">>> Settlement failed: {e}")
        # Delivery was successful, just return it
        return delivery
