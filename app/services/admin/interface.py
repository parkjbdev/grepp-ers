from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.models.reservation_model import ReservationDto
from app.models.slot_model import Slot


class AdminExamManagementService(ABC):
    @abstractmethod
    async def add_exam_slot(self, slot: Slot): pass

    @abstractmethod
    async def delete_exam_slot(self, slot_id: int): pass

    @abstractmethod
    async def find_reservations(self, start_at: Optional[datetime], end_at: Optional[datetime]): pass

    @abstractmethod
    async def modify_reservation(self, id: int, reservation: ReservationDto): pass

    @abstractmethod
    async def delete_reservation(self, reservation_id: int): pass

    @abstractmethod
    async def confirm_reservation(self, reservation_id: int): pass
