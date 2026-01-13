import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.commitment import Commitment
from app.schemas.commitment import CommitmentCreate, CommitmentResponse
from app.services.state import assert_transition
from app.services.razorpay_client import client
from app.models.payment import Payment



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
        raise HTTPException(409, f"Cannot fund in status '{c.status}'")

    # move state
    c.status = "funded"
    db.commit()

    # create Razorpay order (amount in paise)
    order = client.order.create({
        "amount": int(c.amount * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    payment = Payment(
        commitment_id=c.id,
        order_id=order["id"],
        amount=c.amount,
        status="created"
    )
    db.add(payment)
    db.commit()

    return {
        "status": "funded",
        "order_id": order["id"],
        "razorpay_key": os.getenv("RAZORPAY_KEY_ID"),
        "amount": int(c.amount * 100),
        "currency": "INR"
    }


@router.post("/{commitment_id}/lock")
def lock_commitment(
    commitment_id: int,
    db: Session = Depends(get_db),
):
    commitment = (
        db.query(Commitment)
        .filter(Commitment.id == commitment_id)
        .one_or_none()
    )

    if not commitment:
        raise HTTPException(404, "Commitment not found")

    if commitment.status != "paid":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot lock commitment in status '{commitment.status}'",
        )

    commitment.status = "locked"
    db.commit()

    return {
        "id": commitment.id,
        "status": commitment.status,
    }

@router.post("/{commitment_id}/deliver")
def deliver_commitment(
    commitment_id: int,
    db: Session = Depends(get_db),
):
    commitment = (
        db.query(Commitment)
        .filter(Commitment.id == commitment_id)
        .one_or_none()
    )

    if not commitment:
        raise HTTPException(404, "Commitment not found")

    if commitment.status != "locked":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot deliver commitment in status '{commitment.status}'",
        )

    commitment.status = "delivered"
    db.commit()

    return {
        "id": commitment.id,
        "status": commitment.status,
    }


@router.get("/{commitment_id}", response_model=CommitmentResponse)
def get_commitment(commitment_id: int, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")
    return c
