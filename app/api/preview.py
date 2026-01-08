from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.schemas.preview import CommitmentPreview
from app.services.decay import calculate_time_decay_payout
from app.services.settlement import DEFAULT_DECAY_CURVE

router = APIRouter(prefix="/commitments", tags=["preview"])


@router.get("/{commitment_id}/preview", response_model=CommitmentPreview)
def preview_commitment(commitment_id: int, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")

    now = datetime.now(timezone.utc)

    # If already settled, preview is meaningless
    if c.status == "settled":
        raise HTTPException(409, "Commitment already settled")

    delivery = (
        db.query(Delivery)
        .filter(Delivery.commitment_id == c.id)
        .first()
    )

    delivered_at = delivery.submitted_at if delivery else now

    result = calculate_time_decay_payout(
        amount=Decimal(c.amount),
        deadline=c.deadline,
        delivered_at=delivered_at,
        decay_curve=DEFAULT_DECAY_CURVE,
    )

    return CommitmentPreview(
        commitment_id=c.id,
        status=c.status,
        now=now,
        deadline=c.deadline,
        delay_minutes=result["delay_minutes"] or 0,
        expected_payout=result["payout"],
        expected_refund=result["refund"],
    )
