from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class CommitmentCreate(BaseModel):
    client_id: int
    freelancer_id: int
    amount: Decimal
    deadline: datetime
    decay_curve: str = "default"


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
