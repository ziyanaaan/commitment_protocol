from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from pydantic import validator



class CommitmentCreate(BaseModel):
    client_id: int
    freelancer_id: int
    amount: Decimal
    deadline: datetime
    decay_curve: str = "default"
    @validator("deadline")
    def deadline_must_be_utc(cls, v):
        if v.tzinfo is None:
            raise ValueError("deadline must be timezone-aware (UTC)")
        return v



class CommitmentResponse(BaseModel):
    id: int
    client_id: int
    freelancer_id: int
    amount: Decimal
    deadline: datetime
    decay_curve: str
    status: str

    class Config:
        orm_mode = True
