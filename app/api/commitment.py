from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.commitment import Commitment
from app.schemas.commitment import CommitmentCreate, CommitmentResponse
from app.services.state import assert_transition


router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.post("", response_model=CommitmentResponse)
def create_commitment(payload: CommitmentCreate, db: Session = Depends(get_db)):
    c = Commitment(
        client_id=payload.client_id,
        freelancer_id=payload.freelancer_id,
        amount=payload.amount,
        deadline=payload.deadline,
        decay_curve=payload.decay_curve,
        status="draft",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.post("/{commitment_id}/fund")
def fund_commitment(commitment_id: int, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")

    if c.status != "draft":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot fund commitment in status '{c.status}'",
        )

    assert_transition(c.status, "funded")
    c.status = "funded"
    db.commit()
    return {"previous": "draft", "current": "funded"}


@router.post("/{commitment_id}/lock")
def lock_commitment(commitment_id: int, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")

    if c.status != "funded":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot lock commitment in status '{c.status}'",
        )

    assert_transition(c.status, "locked")
    c.status = "locked"
    db.commit()
    return {"previous": "funded", "current": "locked"}


@router.get("/{commitment_id}", response_model=CommitmentResponse)
def get_commitment(commitment_id: int, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")
    return c
