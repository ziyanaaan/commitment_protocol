import stripe
from decimal import Decimal
from app.models.payment import Payment

stripe.api_key = stripe.api_key = __import__("os").getenv("STRIPE_SECRET_KEY")

def create_intent(db, commitment_id: int, amount: Decimal):
    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),
        currency="usd",
        capture_method="manual",
    )
    p = Payment(
        commitment_id=commitment_id,
        intent_id=intent.id,
        amount=amount,
        status="created",
    )
    db.add(p)
    db.commit()
    return intent.client_secret
