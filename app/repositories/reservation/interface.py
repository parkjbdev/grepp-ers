from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.models.reservation_model import Reservation, ReservationDto


class ReservationRepository(ABC):
    @abstractmethod
    async def find(self, user_id: Optional[int] = None, start_at: Optional[datetime] = None,
                   end_at: Optional[datetime] = None): pass

    @abstractmethod
    async def find_by_id(self, reservation_id: int): pass

    @abstractmethod
    async def find_reservation_by_slot(self, slot_id: int, confirmed: bool): pass

    @abstractmethod
    async def insert(self, reservation: Reservation): pass

    @abstractmethod
    async def insert_if_days_left(self, reservation: Reservation, days_left: int): pass

    @abstractmethod
    async def confirm_by_id(self, reservation_id: int): pass

    @abstractmethod
    async def modify_from_admin(self, id: int, reservation: ReservationDto): pass

    @abstractmethod
    async def modify_unconfirmed_if_user_match(self, id: int, reservation: ReservationDto, user_id: int): pass

    @abstractmethod
    async def modify_unconfirmed_if_days_left_and_user_match(self, reservation_id: int, reservation: ReservationDto, user_id: int,
                                                             days: int): pass

    @abstractmethod
    async def delete_from_admin(self, reservation_id: int): pass

    @abstractmethod
    async def delete_unconfirmed(self, reservation_id: int, user_id: int): pass
