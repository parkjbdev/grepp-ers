from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    id: Optional[int] = None
    username: str
    password: Optional[str] = None
    admin: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
