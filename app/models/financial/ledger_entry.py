"""
FinancialLedgerEntry ORM Model - Append-only financial source of truth.

CRITICAL: This table is APPEND-ONLY. Never update or delete entries.
NOTE: This uses the NEW UUID-based schema, not the old Integer-based one.
"""

from sqlalchemy import Column, String, BigInteger, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class FinancialLedgerEntry(Base):
    """
    Append-only ledger for all financial transactions.
    
    Every money movement MUST create a ledger entry.
    Entries are immutable - never update or delete.
    
    NOTE: Table name is 'ledger_entries' matching the new migration.
    Uses extend_existing to coexist with old model during transition.
    """
    __tablename__ = "ledger_entries"
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    commitment_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Type of ledger entry
    # Valid: payment_credit, hold_debit, hold_release, payout_debit, refund_debit, fee_debit, adjustment, reversal
    entry_type = Column(String, nullable=False)
    
    # Amount in smallest currency unit (e.g., paise for INR)
    # ALWAYS positive - direction indicates credit/debit
    amount = Column(BigInteger, nullable=False)
    
    currency = Column(String, nullable=False, default="INR")
    
    # 'credit' or 'debit'
    direction = Column(String, nullable=False)
    
    # Reference to the source record
    reference_table = Column(String, nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    
    created_at = Column(
        String,  # TIMESTAMPTZ stored as string in SQLAlchemy
        nullable=False,
        server_default=func.now()
    )
    
    def __repr__(self):
        return f"<LedgerEntry {self.id}: {self.direction} {self.amount} {self.entry_type}>"
