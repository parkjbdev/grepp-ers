from typing import Annotated

from asyncpg import Connection, RaiseError
from fastapi.params import Depends

from app.database.ers_db import Database
from app.dependencies.config import database
from app.models.reservation_model import Reservation
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.repositories.reservation.interface import ReservationRepository
from app.utils.decorators import singleton


@singleton
class ReservationRepositoryImpl(ReservationRepository):
    def __init__(self, db: Annotated[Database, Depends(lambda: database())]):
        self.__pool = db.get_pool()

    async def find(self):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetch("SELECT * FROM reservations")

    async def find_by_id(self, reservation_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetchrow("SELECT * FROM reservations WHERE id = $1", reservation_id)

    async def find_reservation_by_slot(self, slot_id: int, confirmed: bool):
        # TODO: DTO for return type
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetchrow(
                "SELECT * FROM reservations r JOIN slots s ON r.slot_id = s.id WHERE slot_id = $1 AND confirmed = $2",
                slot_id,
                confirmed)

    async def insert(self, reservation: Reservation):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                return await conn.execute("INSERT INTO reservations(slot_id, user_id, amount) VALUES($1, $2, $3)",
                                          reservation.slot_id, reservation.user_id, reservation.amount)
            except RaiseError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException()
                raise

    async def confirm_by_id(self, reservation_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                return await conn.execute("UPDATE reservations SET confirmed = $1 WHERE id = $2", True, reservation_id)
            except RaiseError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException()
                raise

    async def modify(self, reservation: Reservation):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                return await conn.execute(
                    "UPDATE reservations SET (amount, slot_id) = ($1, $2) WHERE id = $3",
                    reservation.amount, reservation.slot_id, reservation.id)
            except RaiseError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException()
                raise

    async def delete(self, reservation_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.execute("DELETE reservation WHERE id = $1", reservation_id)
