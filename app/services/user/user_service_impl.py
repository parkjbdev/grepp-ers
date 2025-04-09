import logging
from datetime import datetime
from typing import Optional

from asyncpg import PostgresError
from fastapi import Depends

from app.models.reservation_model import Reservation, ReservationDto
from app.models.slot_model import SlotWithAmount
from app.models.slot_reservation_joined_model import ReservationWithSlot
from app.repositories.reservation.dbimpl import ReservationRepository
from app.repositories.reservation.exceptions import DaysNotLeftEnoughException, NoSuchReservationException, \
    ReservationAlreadyConfirmedException, \
    SlotLimitExceededException, UserMismatchException
from app.repositories.slot.dbimpl import SlotRepository
from app.repositories.slot.exceptions import NoSuchSlotException
from app.services.exceptions import DBConflictException, DBUnknownException, NotFoundException
from app.services.user.interface import ExamManagementService


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
        try:
            rows = await self.slot_repo.find(start_at=start_at, end_at=end_at)
            return [SlotWithAmount(**dict(row)) for row in rows]
        except PostgresError as e:
            raise DBUnknownException()

    async def find_slot_by_id(self, slot_id: int):
        try:
            row = await self.slot_repo.find_by_id(slot_id)
            return SlotWithAmount(**dict(row))
        except NoSuchSlotException as e:
            raise NotFoundException(str(e))
        except PostgresError as e:
            raise DBUnknownException(str(e))

    async def find_reservations(self, user_id: int, start_at: Optional[datetime],
                                end_at: Optional[datetime]):
        try:
            rows = await self.reservation_repo.find(user_id=user_id, start_at=start_at, end_at=end_at)
            return [ReservationWithSlot(**dict(row)) for row in rows]
        except PostgresError as e:
            raise DBUnknownException(str(e))

    async def find_reservation_by_id(self, reservation_id: int, user_id: Optional[int] = None):
        try:
            row = await self.reservation_repo.find_by_id(reservation_id, user_id=user_id)
            return ReservationWithSlot(**dict(row))
        except NoSuchReservationException as e:
            raise NotFoundException(str(e))

    async def add_reservation(self, reservation: Reservation):
        try:
            await self.reservation_repo.insert_if_days_left(reservation, 3)
        except NoSuchSlotException as e:
            raise NotFoundException(str(e))
        except (DaysNotLeftEnoughException, SlotLimitExceededException) as e:
            raise DBConflictException(str(e))
        except PostgresError as e:
            raise DBUnknownException(str(e))

    async def modify_reservation(self, id: int, reservation: ReservationDto, user_id: int):
        # async def modify_reservation(self, reservation: Reservation, user_id: int):
        # user can modify only user's own unconfirmed reservation
        try:
            await self.reservation_repo.modify_unconfirmed_if_days_left_and_user_match(id, reservation, user_id, 3)
        except (NoSuchReservationException, NoSuchSlotException) as e:
            raise NotFoundException(str(e))
        except (SlotLimitExceededException, ReservationAlreadyConfirmedException, UserMismatchException,
                DaysNotLeftEnoughException) as e:
            raise DBConflictException(str(e))
        except PostgresError as e:
            raise DBUnknownException()

    async def delete_reservation(self, reservation_id: int, user_id: int):
        # user can delete only user's own unconfirmed reservation
        try:
            await self.reservation_repo.delete_unconfirmed(reservation_id, user_id)
        except NoSuchReservationException as e:
            raise NotFoundException(str(e))
        except (ReservationAlreadyConfirmedException, UserMismatchException) as e:
            raise DBConflictException(str(e))
        except PostgresError as e:
            raise DBUnknownException(str(e))
