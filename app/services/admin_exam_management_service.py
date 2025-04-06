import logging
from abc import ABC, abstractmethod
from datetime import datetime, UTC, timedelta

from asyncpg import ExclusionViolationError

from app.models.reservation_model import Reservation
from app.models.slot_model import Slot
from app.repositories.reservation.dbimpl import ReservationRepository
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.repositories.slot.dbimpl import SlotRepository


class AdminExamManagementService(ABC):
    @abstractmethod
    async def add_exam_slot(self, slot: Slot): pass

    @abstractmethod
    async def find_reservations(self, start_at: datetime, end_at: datetime): pass

    @abstractmethod
    async def modify_reservation(self, reservation: Reservation): pass

    @abstractmethod
    async def delete_reservation(self, reservation_id: int): pass

    @abstractmethod
    async def confirm_reservation(self, reservation_id: int): pass


class AdminExamManagementServiceImpl(AdminExamManagementService):
    def __init__(self, slot_repo: SlotRepository, reservation_repo: ReservationRepository):
        self.slot_repo = slot_repo
        self.reservation_repo = reservation_repo
        self.__logger = logging.getLoggerClass()

    async def add_exam_slot(self, slot: Slot):
        try:
            await self.slot_repo.insert(slot)
        except ExclusionViolationError as e:
            self.__logger.exception(
                f"Time slot conflict: The time range {slot.time_range} overlaps with an existing slot")
            raise

    async def find_reservations(
            self,
            start_at: datetime = datetime.now(UTC),
            end_at: datetime = datetime.now(UTC) + timedelta(days=30)
    ):
        await self.reservation_repo.find()

    async def modify_reservation(self, reservation: Reservation):
        # TODO: admin can modify both confirmed/unconfirmed reservation
        # TODO: user can modify only user's own unconfirmed reservation
        try:
            await self.reservation_repo.modify(reservation)
        except SlotLimitExceededException as e:
            self.__logger.exception(
                f"Slot limit exceeded: The time slot {reservation.slot_id} has reached its maximum capacity")
            raise

    async def delete_reservation(self, reservation_id: int):
        # TODO: admin can delete both confirmed/unconfirmed reservation
        # TODO: user can delete only user's own unconfirmed reservation
        await self.reservation_repo.delete(reservation_id)

    # Admin
    async def confirm_reservation(self, reservation_id: int):
        # TODO: only admin can confirm reservation
        await self.reservation_repo.confirm_by_id(reservation_id)
