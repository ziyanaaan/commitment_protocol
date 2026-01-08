from pydantic import BaseModel


class DeliveryCreate(BaseModel):
    artifact_type: str
    artifact_reference: str
