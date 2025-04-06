import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timezone
from typing import Optional

from asyncpg import ExclusionViolationError
from asyncpg.pgproto.pgproto import timedelta
from fastapi import Depends

from app.models.reservation_model import Reservation
from app.models.slot_model import Slot
from app.repositories.reservation.dbimpl import ReservationRepository
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.repositories.slot.dbimpl import SlotRepository


class ExamManagementService(ABC):
    @abstractmethod
    async def find_slots(self, start_at: datetime, end_at: datetime): pass

    @abstractmethod
    async def find_reservations(self): pass

    @abstractmethod
    async def add_exam_slot(self, slot: Slot): pass

    @abstractmethod
    async def add_reservation(self, reservation: Reservation): pass

    @abstractmethod
    async def modify_reservation(self, reservation: Reservation): pass

    @abstractmethod
    async def delete_reservation(self, reservation_id: int): pass

    @abstractmethod
    async def confirm_reservation(self, reservation_id: int): pass


class ExamManagementServiceImpl(ExamManagementService):
    def __init__(self, slot_repo: SlotRepository = Depends(), reservation_repo: ReservationRepository = Depends()):
        self.slot_repo = slot_repo
        self.reservation_repo = reservation_repo
        self.__logger = logging.getLoggerClass()

    async def find_slots(
            self,
            start_at: datetime,
            end_at: datetime
    ):
        return await self.slot_repo.find_by_time_range(start_at, end_at)

    async def find_reservations(self):
        return await self.reservation_repo.find()

    async def add_exam_slot(self, slot: Slot):
        try:
            return await self.slot_repo.insert(slot)
        except ExclusionViolationError as e:
            self.__logger.exception(
                f"Time slot conflict: The time range {slot.time_range} overlaps with an existing slot")
            raise
        except Exception as e:
            self.__logger.exception(f"Unknown Exception: {e}")

    async def add_reservation(self, reservation: Reservation):
        try:
            return await self.reservation_repo.insert(reservation)
        except SlotLimitExceededException as e:
            self.__logger.exception(
                f"Slot limit exceeded: The slot limit 50000 exceeded"
            )
            raise

    async def modify_reservation(self, reservation: Reservation):
        # TODO: admin can modify both confirmed/unconfirmed reservation
        # TODO: user can modify only user's own unconfirmed reservation
        await self.reservation_repo.modify(reservation)

    async def delete_reservation(self, reservation_id: int):
        # TODO: admin can delete both confirmed/unconfirmed reservation
        # TODO: user can delete only user's own unconfirmed reservation
        await self.reservation_repo.delete(reservation_id)

    # Admin
    async def confirm_reservation(self, reservation_id: int):
        # TODO: only admin can confirm reservation
        await self.reservation_repo.confirm_by_id(reservation_id)
