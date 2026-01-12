import hmac
import hashlib
import os

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.payment import Payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/verify")
def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    db: Session = Depends(get_db),
):
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

    if expected_signature != razorpay_signature:
        raise HTTPException(400, "Invalid payment signature")

    # Mark payment as verified
    payment.payment_id = razorpay_payment_id
    payment.status = "paid"

    db.add(payment)
    db.commit()

    return {"status": "verified"}
