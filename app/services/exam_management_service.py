import logging
from abc import ABC, abstractmethod
from datetime import datetime

from fastapi import Depends

from app.models.reservation_model import Reservation
from app.models.slot_model import SlotWithAmount
from app.models.slot_reservation_joined_model import ReservationWithSlot
from app.repositories.reservation.dbimpl import ReservationRepository
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.repositories.slot.dbimpl import SlotRepository


class ExamManagementService(ABC):
    @abstractmethod
    async def find_slots(self, start_at: datetime, end_at: datetime): pass

    @abstractmethod
    async def find_reservations(self, user_id: int, start_at: datetime = None, end_at: datetime = None): pass

    @abstractmethod
    async def add_reservation(self, reservation: Reservation): pass

    @abstractmethod
    async def modify_reservation(self, reservation: Reservation, user_id: int): pass

    @abstractmethod
    async def delete_reservation(self, reservation_id: int, user_id: int): pass


class ExamManagementServiceImpl(ExamManagementService):
    def __init__(self, slot_repo: SlotRepository = Depends(), reservation_repo: ReservationRepository = Depends()):
        self.slot_repo = slot_repo
        self.reservation_repo = reservation_repo
        self.__logger = logging.getLogger(__name__)

    async def find_slots(
            self,
            start_at: datetime,
            end_at: datetime
    ):
        rows = await self.slot_repo.find(start_at=start_at, end_at=end_at)
        return [SlotWithAmount(**dict(row)) for row in rows]

    async def find_reservations(self, user_id: int, start_at: datetime = None, end_at: datetime = None):
        rows = await self.reservation_repo.find(user_id=user_id, start_at=start_at, end_at=end_at)
        return [ReservationWithSlot(**dict(row)) for row in rows]

    async def add_reservation(self, reservation: Reservation):
        try:
            ret = await self.reservation_repo.insert(reservation)
            if ret is None:
                raise Exception("Failed to insert reservation")
        except SlotLimitExceededException as e:
            self.__logger.exception(
                f"Slot limit exceeded: The slot limit 50000 exceeded"
            )
            raise

    async def modify_reservation(self, reservation: Reservation, user_id: int):
        # user can modify only user's own unconfirmed reservation
        try:
            ret = await self.reservation_repo.modify(reservation, user_id)
            if ret is None:
                raise Exception("Failed to modify reservation.. Is it already confirmed?")
        except KeyError as e:
            self.__logger.exception(f"Reservation not found: {reservation.id}")
            raise

    async def delete_reservation(self, reservation_id: int, user_id: int):
        # user can delete only user's own unconfirmed reservation
        try:
            await self.reservation_repo.delete(reservation_id, user_id)
        except KeyError as e:
            self.__logger.exception(f"Reservation not found: {reservation_id}")
            raise
