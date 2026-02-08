"""
BeneficiaryAccount ORM Model - Payout destination references.

CRITICAL: This table stores ONLY gateway tokens, NEVER raw bank details.
"""

from sqlalchemy import Column, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class BeneficiaryAccount(Base):
    """
    Beneficiary account for payouts.
    
    Stores ONLY gateway token references (contact_id, fund_account_id).
    NEVER stores raw bank details, UPI IDs, or PAN.
    """
    __tablename__ = "beneficiary_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Gateway token references only
    gateway_contact_id = Column(String, nullable=False)
    gateway_fund_account_id = Column(String, nullable=False)
    
    # Valid: bank_account, vpa, wallet
    account_type = Column(String, nullable=False)
    
    is_primary = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(String, nullable=False, server_default=func.now())
    
    def __repr__(self):
        return f"<BeneficiaryAccount {self.id}: {self.account_type} primary={self.is_primary}>"
