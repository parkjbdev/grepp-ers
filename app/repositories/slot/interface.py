from abc import ABC, abstractmethod
from datetime import datetime

from app.models.slot_model import Slot


class SlotRepository(ABC):
    @abstractmethod
    async def find(self): pass

    @abstractmethod
    async def find_by_time_range(self, start_at: datetime, end_at: datetime): pass

    @abstractmethod
    async def find_by_id(self, slot_id: int): pass

    @abstractmethod
    async def insert(self, slot: Slot): pass

    @abstractmethod
    async def modify(self, slot: Slot): pass

    @abstractmethod
    async def delete(self, slot_id: int): pass

    @abstractmethod
    async def count_confirmed_slot(self): pass
