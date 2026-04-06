from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.commitment import Commitment
from app.models.settlement import Settlement
from app.models.user import User
from app.services.settlement import settle_commitment

router = APIRouter(prefix="/settlements", tags=["settlements"])


@router.get("/by-commitment/{commitment_id}")
def get_by_commitment(
    commitment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get settlement by commitment ID.
    Only parties involved in the commitment can view the settlement.
    """
    # First check authorization
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")
    
    # Authorization: compare public_id
    if current_user.role != "admin":
        if c.client_id != current_user.public_id and c.freelancer_id != current_user.public_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this commitment"
            )
    
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
        "Delay_minutes": s.delay_minutes,
        "decay_applied": s.decay_applied,
        "Settled_at": s.settled_at,
    }


@router.post("/{commitment_id}/settle")
def settle(
    commitment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger settlement for a commitment.
    Only the freelancer or admin can trigger settlement.
    """
    # Check authorization
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")
    
    # Authorization: compare public_id
    if current_user.role != "admin":
        if c.freelancer_id != current_user.public_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the freelancer or admin can trigger settlement"
            )
    
    try:
        settlement = settle_commitment(db, commitment_id)

        if settlement is None:
            raise HTTPException(500, "Settlement failed to create")

        return {
            "status": "ok",
            "settlement_id": settlement.id,
            "payout": float(settlement.payout_amount),
            "refund": float(settlement.refund_amount),
        }

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{commitment_id}/financial-status")
def get_financial_status(
    commitment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the financial status for a commitment.
    Shows payment, payout, and refund statuses.
    Only parties involved in the commitment can view this.
    """
    # Check authorization
    c = db.query(Commitment).filter_by(id=commitment_id).first()
    if not c:
        raise HTTPException(404, "Commitment not found")
    
    # Authorization: compare public_id
    if current_user.role != "admin":
        if c.client_id != current_user.public_id and c.freelancer_id != current_user.public_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this commitment"
            )
    
    # Get payment status
    payment_result = db.execute(
        text("""
            SELECT status FROM payments
            WHERE commitment_id = :commitment_id
            ORDER BY created_at DESC LIMIT 1
        """),
        {"commitment_id": commitment_id}
    )
    payment_row = payment_result.fetchone()
    payment_status = payment_row[0] if payment_row else "pending"
    
    # Get payout status
    payout_result = db.execute(
        text("""
            SELECT status, amount FROM payouts
            WHERE commitment_id = :commitment_id
            ORDER BY created_at DESC LIMIT 1
        """),
        {"commitment_id": commitment_id}
    )
    payout_row = payout_result.fetchone()
    payout_status = payout_row[0] if payout_row else None
    payout_amount = int(payout_row[1]) if payout_row else None
    
    # Get refund status
    refund_result = db.execute(
        text("""
            SELECT status, amount FROM refunds
            WHERE commitment_id = :commitment_id
            ORDER BY created_at DESC LIMIT 1
        """),
        {"commitment_id": commitment_id}
    )
    refund_row = refund_result.fetchone()
    refund_status = refund_row[0] if refund_row else None
    refund_amount = int(refund_row[1]) if refund_row else None
    
    return {
        "payment_status": payment_status,
        "payout_status": payout_status,
        "payout_amount": payout_amount,
        "refund_status": refund_status,
        "refund_amount": refund_amount,
    }
