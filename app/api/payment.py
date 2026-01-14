import hmac
import hashlib
import os

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.payment import Payment
from app.models.commitment import Commitment
from app.schemas.payment import RazorpayVerifyRequest



router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/verify")
def verify_payment(
    payload: RazorpayVerifyRequest,
    db: Session = Depends(get_db),
):  
    razorpay_order_id = payload.razorpay_order_id
    razorpay_payment_id = payload.razorpay_payment_id
    razorpay_signature = payload.razorpay_signature

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == razorpay_order_id)
        .one_or_none()
    )
    if not payment:
        raise HTTPException(404, "Payment record not found")

    # Generate expected signature
    secret = os.getenv("RAZORPAY_KEY_SECRET")
    message = f"{razorpay_order_id}|{razorpay_payment_id}"

    expected_signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # UPDATE PAYMENT RECORD
    payment.payment_id = razorpay_payment_id
    payment.status = "paid"

    # UPDATE COMMITMENT
    commitment = db.query(Commitment).filter(
        Commitment.id == payment.commitment_id
    ).one()

    commitment.status = "paid"

    db.commit()


    return {
        "ok": True,
        "payment_status": payment.status,
        "commitment_status": commitment.status,


    }


@router.get("/{commitment_id}")
def get_payment(commitment_id: int, db: Session = Depends(get_db)):
        payment = (
            db.query(Payment)
            .filter(Payment.commitment_id == commitment_id)
            .one_or_none()
        )  

        if not payment:
            raise HTTPException(404, "Payment not found")

        return {
            "status": payment.status,
            "order_id": payment.order_id,
            "payment_id": payment.payment_id,
            "amount": float(payment.amount),
        }

