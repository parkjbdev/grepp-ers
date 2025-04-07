from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Reservation(BaseModel):
    id: Optional[int] = None
    slot_id: int
    user_id: int
    amount: int = 0
    confirmed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator('amount')
    def amount_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('amount must be greater than or equal to 0')
        return v


class ReservationDto(BaseModel):
    slot_id: int
    amount: int
