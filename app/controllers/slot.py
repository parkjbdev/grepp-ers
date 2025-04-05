from datetime import datetime
from typing import Optional

from fastapi import APIRouter

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.get("")
async def get_available_slots(start_at: Optional[datetime] = datetime.now(), end_at: Optional[datetime] = None):
    return


@router.post("")
async def add_new_slot():
    return
