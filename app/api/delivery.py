from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.schemas.delivery import DeliveryCreate

router = APIRouter(prefix="/commitments", tags=["delivery"])


@router.post("/{commitment_id}/deliver")
def deliver(commitment_id: int, payload: DeliveryCreate, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")

    if c.status != "locked":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot deliver commitment in status '{c.status}'",
        )

    existing = db.query(Delivery).filter_by(commitment_id=commitment_id).first()
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Delivery already submitted",
        )

    d = Delivery(
        commitment_id=commitment_id,
        artifact_type=payload.artifact_type,
        artifact_reference=payload.artifact_reference,
    )
    c.status = "delivered"
    db.add(d)
    db.commit()
    return {"previous": "locked", "current": "delivered"}
