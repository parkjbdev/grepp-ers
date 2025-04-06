from datetime import datetime
from typing import Optional

from asyncpg.types import Range
from pydantic import BaseModel, Field, field_serializer, field_validator


class ReservationWithSlot(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    # Reservation fields
    id: Optional[int] = None
    slot_id: int
    user_id: int
    amount: int = 0
    confirmed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    # Slot fields
    time_range: Range

    @field_validator('amount')
    def amount_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('amount must be greater than or equal to 0')
        return v

    @classmethod
    @field_validator("time_range", mode="before")
    def validate_time_range(cls, v):
        if isinstance(v, Range):
            return v
        raise TypeError(f"Expected Range, got {type(v)}")

    @field_serializer('time_range')
    def serialize_time_range(self, v: Range, _info):
        return {
            "start": v.lower,
            "end": v.upper,
            "start_inclusive": v.lower_inc,
            "end_inclusive": v.upper_inc,
        }
