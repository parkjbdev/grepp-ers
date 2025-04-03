from typing import Optional
from pydantic import BaseModel
from asyncpg.types import Range


class Slot(BaseModel):
    id: Optional[int] = None
    time_range: Range
