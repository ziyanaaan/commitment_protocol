from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class CommitmentPreview(BaseModel):
    commitment_id: int
    status: str
    now: datetime
    deadline: datetime
    delay_minutes: int
    expected_payout: Decimal
    expected_refund: Decimal
