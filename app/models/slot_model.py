import datetime
from typing import Optional
from pydantic import BaseModel, field_serializer, field_validator
from asyncpg.types import Range


class _Slot(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    time_range: Range

    @classmethod
    @field_validator("time_range", mode="before")
    def validate_time_range(cls, v):
        if isinstance(v, Range):
            return v
        raise TypeError(f"Expected Range, got {type(v)}")

    @field_serializer("time_range")
    def serialize_time_range(self, v: Range, _info):
        return {
            "start": v.lower,
            "end": v.upper,
            "start_inclusive": v.lower_inc,
            "end_inclusive": v.upper_inc,
        }


class Slot(_Slot):
    id: Optional[int] = None

    @classmethod
    def create_with_time_range(cls, start_time: datetime, end_time: datetime, id: Optional[int] = None):
        time_range = Range(lower=start_time, upper=end_time, lower_inc=True, upper_inc=False)
        return cls(id=id, time_range=time_range)


class SlotWithAmount(Slot):
    amount: int


class _TimeRangeSchema(BaseModel):
    start: datetime.datetime
    end: datetime.datetime
    start_inclusive: bool
    end_inclusive: bool


class SlotForResponse(BaseModel):
    id: int
    time_range: _TimeRangeSchema
    amount: int

    @classmethod
    def from_slot_with_amount(cls, slot_with_amount: SlotWithAmount):
        return cls(
            id=slot_with_amount.id,
            time_range=_TimeRangeSchema(
                start=slot_with_amount.time_range.lower,
                end=slot_with_amount.time_range.upper,
                start_inclusive=slot_with_amount.time_range.lower_inc,
                end_inclusive=slot_with_amount.time_range.upper_inc,
            ),
            amount=slot_with_amount.amount
        )
