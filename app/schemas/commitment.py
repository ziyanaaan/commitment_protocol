from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from pydantic import validator
from typing import Optional



class CommitmentCreate(BaseModel):
    client_id: str  # Changed from int to str (public_id)
    freelancer_id: str  # Changed from int to str (public_id)
    amount: Decimal
    deadline: datetime
    title: str
    description: Optional[str] = None
    decay_curve: str = "balanced"
    @validator("deadline")
    def deadline_must_be_utc(cls, v):
        if v.tzinfo is None:
            raise ValueError("deadline must be timezone-aware (UTC)")
        return v



class CommitmentResponse(BaseModel):
    id: int
    client_id: str  # Changed from int to str (public_id)
    freelancer_id: str  # Changed from int to str (public_id)
    amount: Decimal
    deadline: datetime
    title: str
    description: Optional[str] = None
    decay_curve: str = "balanced"
    status: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
