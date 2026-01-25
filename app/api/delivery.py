from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.schemas.delivery import DeliveryCreate
from app.services.state import assert_transition
from app.services.delivery import deliver_commitment


router = APIRouter(prefix="/commitments", tags=["delivery"])


@router.post("/{commitment_id}/deliver_commitment")
def deliver_commitment(
    commitment_id: int,
    payload: DeliveryCreate,
    db: Session = Depends(get_db),
):
    delivery = deliver_commitment(db=db, commitment_id=commitment_id, payload=payload)

    return {
        "id": delivery.id,
        "status": "delivered",
        "delivered_at": delivery.submitted_at,
    }
