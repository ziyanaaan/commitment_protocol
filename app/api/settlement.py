from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.settlement import Settlement

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.get("/by-commitment/{commitment_id}")
def get_by_commitment(commitment_id: int, db: Session = Depends(get_db)):
    s = (
        db.query(Settlement)
        .filter(Settlement.commitment_id == commitment_id)
        .one_or_none()
    )
    if not s:
        raise HTTPException(404, "Settlement not found")
    return {
        "commitment_id": s.commitment_id,
        "payout_amount": float(s.payout_amount),
        "refund_amount": float(s.refund_amount),
        "decay_applied": s.decay_applied,
        "created_at": s.created_at,
    }
