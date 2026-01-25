import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.schemas.commitment import CommitmentCreate, CommitmentResponse
from app.services.state import assert_transition
from app.services.razorpay_client import client
from app.models.payment import Payment
from app.services.delivery import deliver_commitment
from app.schemas.delivery import DeliveryCreate


class CommitmentCreateRequest(BaseModel):
    client_id: int
    freelancer_id: int
    amount: float
    deadline: datetime
    title: str
    description: str
    decay_curve: str = "linear"

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.post("")
def create_commitment(payload: CommitmentCreateRequest, db: Session = Depends(get_db)):
    c = Commitment(
        client_id=payload.client_id,
        freelancer_id=payload.freelancer_id,
        amount=payload.amount,
        deadline=payload.deadline,
        title=payload.title,
        description=payload.description,
        decay_curve=payload.decay_curve,
        status="draft",
    )
    if payload.client_id is None:
        raise HTTPException(400, "client_id is required")

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
def deliver(
    commitment_id: int,
    payload: DeliveryCreate | None = None,
    db: Session = Depends(get_db),
):
    """Deliver a commitment. Idempotent - safe to call multiple times."""
    if payload is None:
        payload = DeliveryCreate(
            artifact_type="manual",
            artifact_reference="submitted via UI"
        )

    try:
        result = deliver_commitment(db, commitment_id, payload)
    except ValueError as e:
        # Convert ValueError to HTTPException with proper status
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(404, error_msg)
        else:
            raise HTTPException(409, error_msg)
    
    # Handle both dict return (new delivery) and Delivery object return (existing)
    if isinstance(result, dict):
        delivery = result["delivery"]
        settlement = result.get("settlement")
        return {
            "id": delivery.id,
            "status": "settled",
            "delivered_at": delivery.submitted_at,
            "settlement_id": settlement.id if settlement else None,
        }
    else:
        # Existing delivery was returned (idempotent case)
        return {
            "id": result.id,
            "status": "delivered",
            "delivered_at": result.submitted_at,
            "message": "Already delivered"
        }


@router.get("/{commitment_id}", response_model=CommitmentResponse)
def get_commitment(commitment_id: int, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")
    return c
