from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    commitment_id = Column(Integer, ForeignKey("commitments.id"), unique=True)

    order_id = Column(String, nullable=False)
    payment_id = Column(String, nullable=True)  # filled after payment
    amount = Column(Numeric(10,2), nullable=False)
    status = Column(String, nullable=False)  # created | paid | refunded
