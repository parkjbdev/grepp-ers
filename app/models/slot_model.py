import datetime
from typing import Optional
from pydantic import BaseModel
from asyncpg.types import Range


class Slot(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    id: Optional[int] = None
    time_range: Range

    @classmethod
    def create_with_time_range(cls, start_time: datetime, end_time: datetime, id: Optional[int] = None):
        time_range = Range(lower=start_time, upper=end_time, lower_inc=True, upper_inc=False)
        return cls(id=id, time_range=time_range)
