from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.models.user import User
from app.schemas.preview import CommitmentPreview
from app.services.decay import calculate_time_decay_payout

router = APIRouter(prefix="/commitments", tags=["preview"])


@router.get("/{commitment_id}/preview", response_model=CommitmentPreview)
def preview_commitment(
    commitment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Preview settlement for a commitment.
    Only parties involved in the commitment can preview it.
    """
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")
    
    # Authorization: user must be the client, freelancer, or admin
    if current_user.role != "admin":
        if c.client_id != current_user.id and c.freelancer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this commitment"
            )

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
        decay_curve=c.decay_curve,
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
