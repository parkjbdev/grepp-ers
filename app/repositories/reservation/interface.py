from abc import ABC, abstractmethod

from app.models.reservation_model import Reservation


class ReservationRepository(ABC):
    @abstractmethod
    async def find(self): pass

    @abstractmethod
    async def find_by_id(self, reservation_id: int): pass

    @abstractmethod
    async def insert(self, reservation: Reservation): pass

    @abstractmethod
    async def confirm_by_id(self, reservation_id: int): pass

    @abstractmethod
    async def modify(self, reservation: Reservation): pass

    @abstractmethod
    async def delete(self, reservation_id: int): pass

    @abstractmethod
    async def find_reservation_by_slot(self, slot_id: int, confirmed: bool): pass
