import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from asyncpg import ExclusionViolationError, PostgresError

from app.models.reservation_model import ReservationDto
from app.models.slot_model import Slot
from app.models.slot_reservation_joined_model import ReservationWithSlot
from app.repositories.reservation.dbimpl import ReservationRepository
from app.repositories.reservation.exceptions import NoSuchReservationException, SlotLimitExceededException
from app.repositories.slot.dbimpl import SlotRepository
from app.repositories.slot.exceptions import SlotTimeRangeOverlapped
from app.services.exceptions import DBConflictException, DBUnknownException, NotFoundException


class AdminExamManagementService(ABC):
    @abstractmethod
    async def add_exam_slot(self, slot: Slot): pass

    @abstractmethod
    async def find_reservations(self, start_at: Optional[datetime], end_at: Optional[datetime]): pass

    @abstractmethod
    async def modify_reservation(self, id: int, reservation: ReservationDto): pass

    @abstractmethod
    async def delete_reservation(self, reservation_id: int): pass

    @abstractmethod
    async def confirm_reservation(self, reservation_id: int): pass


class AdminExamManagementServiceImpl(AdminExamManagementService):
    def __init__(self, slot_repo: SlotRepository, reservation_repo: ReservationRepository):
        self.slot_repo = slot_repo
        self.reservation_repo = reservation_repo
        self.__logger = logging.getLogger(__name__)

    async def add_exam_slot(self, slot: Slot):
        try:
            ret = await self.slot_repo.insert(slot)
            if ret is None:
                self.__logger.exception("Failed to insert slot.")
                raise DBUnknownException()
        except SlotTimeRangeOverlapped as e:
            self.__logger.exception(
                f"Time slot conflict: The time range {slot.time_range} overlaps with an existing slot")
            raise DBConflictException(str(e))
        except PostgresError as e:
            raise DBUnknownException()

    async def find_reservations(self, start_at: Optional[datetime], end_at: Optional[datetime]):
        try:
            rows = await self.reservation_repo.find(start_at=start_at, end_at=end_at)
            return [ReservationWithSlot(**dict(row)) for row in rows]
        except PostgresError as e:
            raise DBUnknownException()

    async def modify_reservation(self, id: int, reservation: ReservationDto):
        # admin can modify both confirmed/unconfirmed reservation
        try:
            await self.reservation_repo.modify_from_admin(id, reservation)
        except NoSuchReservationException as e:
            self.__logger.exception(f"Reservation with ID {id} not found.")
            raise NotFoundException(str(e))
        except SlotLimitExceededException as e:
            self.__logger.exception(
                f"Slot limit exceeded: The time slot {reservation.slot_id} has reached its maximum capacity")
            raise DBConflictException(str(e))
        except PostgresError as e:
            raise DBUnknownException()

    async def delete_reservation(self, reservation_id: int):
        # admin can delete both confirmed/unconfirmed reservation
        try:
            await self.reservation_repo.delete_from_admin(reservation_id)
        except NoSuchReservationException as e:
            self.__logger.exception(f"Reservation with ID {reservation_id} not found.")
            raise NotFoundException(str(e))
        except PostgresError as e:
            raise DBUnknownException()

    async def confirm_reservation(self, reservation_id: int):
        # only admin can confirm reservation
        try:
            await self.reservation_repo.confirm_by_id(reservation_id)
        except SlotLimitExceededException as e:
            self.__logger.exception(
                f"Slot limit exceeded: The time slot {reservation_id} has reached its maximum capacity")
            raise
        except PostgresError as e:
            raise DBUnknownException()
