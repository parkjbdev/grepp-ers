from datetime import datetime, timedelta, timezone

from asyncpg import Connection, PostgresError

from app.models.reservation_model import Reservation, ReservationDto
from app.repositories.reservation.dbimpl import ReservationRepositoryImpl
from app.repositories.reservation.exceptions import DaysNotLeftEnoughException, NoSuchReservationException, \
    ReservationAlreadyConfirmedException, \
    SlotLimitExceededException, UserMismatchException
from app.repositories.slot.exceptions import NoSuchSlotException


class ReservationRepositoryTransactionImpl(ReservationRepositoryImpl):
    def __init__(self, pool):
        super().__init__(pool)
        self.__pool = pool

    # Override
    async def insert_if_days_left(self, reservation: Reservation, days_left: int = 3):
        async with self.__pool.acquire() as conn:  # type: Connection
            async with conn.transaction():
                slot_row = await conn.fetchrow("SELECT * FROM slots WHERE id = $1", reservation.slot_id)
                if slot_row is None:
                    raise NoSuchSlotException(reservation.slot_id) from None

                if slot_row["time_range"].lower < datetime.now(timezone.utc) + timedelta(days=days_left):
                    raise DaysNotLeftEnoughException(days_left)

                try:
                    return await conn.fetchrow(
                        "INSERT INTO reservations(slot_id, user_id, amount) VALUES($1, $2, $3) RETURNING id",
                        reservation.slot_id, reservation.user_id, reservation.amount)
                except PostgresError as e:
                    if "SlotLimitExceeded" in str(e):
                        raise SlotLimitExceededException() from None
                    raise

    # Override
    async def modify_unconfirmed_if_days_left_and_user_match(self, reservation_id: int, reservation: ReservationDto,
                                                             user_id: int,
                                                             days_left: int = 3):
        async with self.__pool.acquire() as conn:  # type: Connection
            async with conn.transaction():
                res_row = await conn.fetchrow("SELECT id, user_id, confirmed FROM reservations WHERE id = $1",
                                              reservation_id)
                if res_row is None:
                    raise NoSuchReservationException(reservation_id)
                if res_row["user_id"] != user_id:
                    raise UserMismatchException(user_id)
                if res_row["confirmed"]:
                    raise ReservationAlreadyConfirmedException(reservation_id)

                slot_row = await conn.fetchrow("SELECT * FROM slots WHERE id = $1", reservation.slot_id)

                if slot_row is None:
                    raise NoSuchSlotException(reservation.slot_id)

                if slot_row["time_range"].lower < datetime.now(timezone.utc) + timedelta(days=days_left):
                        raise DaysNotLeftEnoughException(days_left)

                try:
                    ret = await conn.fetchrow(
                        "UPDATE reservations SET (amount, slot_id) = ($1, $2) WHERE id = $3 RETURNING id",
                        reservation.amount, reservation.slot_id, reservation_id)
                    return ret
                except PostgresError as e:
                    if "SlotLimitExceeded" in str(e):
                        raise SlotLimitExceededException() from None
                    raise

    # Override
    async def delete_unconfirmed(self, reservation_id: int, user_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            async with conn.transaction():
                ret = await conn.fetchrow("SELECT id, user_id, confirmed FROM reservations WHERE id = $1",
                                          reservation_id)
                if ret is None:
                    raise NoSuchReservationException(reservation_id)
                if ret["user_id"] != user_id:
                    raise UserMismatchException(user_id)
                if ret["confirmed"]:
                    raise ReservationAlreadyConfirmedException(reservation_id)

                return await conn.fetchrow("DELETE FROM reservations WHERE id = $1 RETURNING id", reservation_id)
