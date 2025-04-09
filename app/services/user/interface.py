from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.models.reservation_model import Reservation, ReservationDto


class ExamManagementService(ABC):
    @abstractmethod
    async def find_slots(self, start_at: datetime, end_at: datetime): pass

    @abstractmethod
    async def find_slot_by_id(self, slot_id: int): pass

    @abstractmethod
    async def find_reservations(self, user_id: int, start_at: Optional[datetime],
                                end_at: Optional[datetime]): pass

    @abstractmethod
    async def find_reservation_by_id(self, reservation_id: int, user_id: Optional[int] = None): pass

    @abstractmethod
    async def add_reservation(self, reservation: Reservation): pass

    @abstractmethod
    async def modify_reservation(self, id: int, reservation: ReservationDto, user_id: int): pass

    @abstractmethod
    async def delete_reservation(self, reservation_id: int, user_id: int): pass
