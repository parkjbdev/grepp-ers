from datetime import datetime, timedelta
from typing import Optional

from asyncpg import Connection, Pool, PostgresError

from app.models.reservation_model import Reservation, ReservationDto
from app.repositories.reservation.exceptions import DaysNotLeftEnoughException, NoSuchReservationException, \
    ReservationAlreadyConfirmedException, \
    SlotLimitExceededException, UserMismatchException
from app.repositories.reservation.interface import ReservationRepository
from app.repositories.slot.exceptions import NoSuchSlotException


class ReservationRepositoryImpl(ReservationRepository):
    def __init__(self, pool: Pool):
        self.__pool = pool

    @staticmethod
    def __joined_query():
        return """
            SELECT 
                r.id AS id, 
                r.slot_id AS slot_id,
                r.user_id AS user_id, 
                r.amount AS amount, 
                r.confirmed AS confirmed, 
                r.created_at AS created_at, 
                r.confirmed_at AS confirmed_at, 
                r.updated_at AS updated_at, 
                s.time_range AS time_range 
            FROM reservations r 
            JOIN slots s ON r.slot_id = s.id
        """

    async def find(self, user_id: Optional[int] = None, start_at: Optional[datetime] = None,
                   end_at: Optional[datetime] = None):
        conditions = []
        params = []

        if user_id is not None:
            params.append(user_id)
            conditions.append(f"r.user_id = ${len(params)}")

        if start_at is not None and end_at is not None:
            params.extend([start_at, end_at])
            conditions.append(f"s.time_range && TSTZRANGE(${len(params) - 1}, ${len(params)})")
        elif start_at is not None:
            params.append(start_at)
            conditions.append(f"UPPER(s.time_range) >= ${len(params)}")
        elif end_at is not None:
            params.append(end_at)
            conditions.append(f"LOWER(s.time_range) <= ${len(params)}")

        base_query = self.__joined_query()
        if conditions:
            base_query += "\nWHERE " + " AND ".join(conditions)

        async with self.__pool.acquire() as conn:  # type: Connection
            rows = await conn.fetch(base_query, *params)
            return rows

    async def find_by_id(self, reservation_id: int):
        base_query = self.__joined_query()
        base_query += "\nWHERE r.id = $1"
        async with self.__pool.acquire() as conn:  # type: Connection
            row = await conn.fetchrow(base_query, reservation_id)
            if row is None:
                raise NoSuchReservationException(reservation_id)
            return row

    async def find_reservation_by_slot(self, slot_id: int, confirmed: bool):
        base_query = self.__joined_query()
        base_query += "\nWHERE slot_id = $1 AND confirmed = $2"
        async with self.__pool.acquire() as conn:
            return await conn.fetch(base_query, slot_id, confirmed)

    async def insert(self, reservation: Reservation):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                ret = await conn.fetchrow(
                    "INSERT INTO reservations(slot_id, user_id, amount) VALUES($1, $2, $3) RETURNING id",
                    reservation.slot_id, reservation.user_id, reservation.amount)
                return ret
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException() from None
                raise

    async def insert_if_days_left(self, reservation: Reservation, days_left: int = 3):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                query = f"""    
WITH decision AS (
    SELECT 
        s.id AS slot_id,
        LOWER(s.time_range) AS start_time
    FROM slots s
    WHERE s.id = $1
),
inserted AS (
    INSERT INTO reservations(slot_id, user_id, amount)
    SELECT d.slot_id, $2, $3
    FROM decision d
    WHERE d.start_time >= (NOW() + INTERVAL '{days_left} days')
    RETURNING id
)
SELECT 
    COALESCE(i.id, d.slot_id) AS id,
    CASE 
        WHEN i.id IS NOT NULL THEN 'inserted'
        WHEN d.slot_id IS NOT NULL THEN 'too_late'
        ELSE NULL
    END AS status
FROM decision d
LEFT JOIN inserted i ON TRUE
"""
                ret = await conn.fetchrow(
                    query,
                    reservation.slot_id, reservation.user_id, reservation.amount)

                if ret is None:
                    raise NoSuchSlotException(reservation.slot_id)
                elif ret["status"] == "too_late":
                    raise DaysNotLeftEnoughException(days_left)
                elif ret["status"] == "inserted":
                    return ret["id"]
            except PostgresError as e:
                print(e)
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException() from None
                raise

    async def modify_unconfirmed_if_user_match(self, reservation_id: int, reservation: ReservationDto, user_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                ret = await conn.fetchrow(
                    """
                    WITH target AS (
                        SELECT * FROM reservations WHERE id = $1
                    ), updated AS (
                        UPDATE reservations r
                        SET (amount, slot_id) = ($3, $4)
                        FROM target
                        WHERE r.id = target.id AND r.user_id = $2 AND r.confirmed = FALSE
                        RETURNING r.id
                    )
                    SELECT 
                    COALESCE(u.id, t.id) AS id,
                    CASE
                        WHEN t.user_id != $2 THEN 'user_mismatch'
                        WHEN t.confirmed = TRUE THEN 'already_confirmed'
                        ELSE 'updated'
                    END AS status
                    FROM target t
                    LEFT JOIN updated u ON t.id = u.id
                    """, reservation_id, user_id, reservation.amount, reservation.slot_id)

                # response: id, status
                if ret is None:
                    raise NoSuchReservationException(reservation_id)
                elif ret["status"] == "already_confirmed":
                    raise ReservationAlreadyConfirmedException(reservation_id)
                elif ret["status"] == "user_mismatch":
                    raise UserMismatchException(user_id)

                return ret
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException() from None
                elif "reservations__slots.id_fk" in str(e):
                    # naive check
                    raise NoSuchSlotException(reservation.slot_id) from None
                raise

    async def modify_unconfirmed_if_days_left_and_user_match(self, reservation_id: int, reservation: ReservationDto,
                                                             user_id: int,
                                                             days: int):
        # AWARE: the query is becoming rubbish... moving to transactionimpl
        # I don't know if it's actually working correctly
        query = """
WITH 
target AS (
    SELECT * 
    FROM reservations 
    WHERE id = $1
),
slot_check AS (
    SELECT * 
    FROM slots 
    WHERE id = $4
),
updated AS (
    UPDATE reservations r
    SET amount = $3, slot_id = $4
    FROM target t, slot_check s
    WHERE r.id = t.id 
      AND t.user_id = $2 
      AND t.confirmed = FALSE
      AND s.id = $4
      AND s.time_range < (NOW() + ($5 || ' days')::INTERVAL)
    RETURNING r.id
)
SELECT 
    COALESCE(u.id, t.id) AS id,
    CASE 
        WHEN t.id IS NULL THEN 'not_found'
        WHEN s.id IS NULL THEN 'no_slot'
        WHEN t.user_id != $2 THEN 'user_mismatch'
        WHEN t.confirmed = TRUE THEN 'already_confirmed'
        WHEN s.time_range >= (NOW() + ($5 || ' days')::INTERVAL) THEN 'days_not_enough'
        ELSE 'updated'
    END AS status
FROM target t
LEFT JOIN updated u ON t.id = u.id
LEFT JOIN slot_check s ON s.id = $4
        """
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                ret = await conn.fetchrow(
                    query,
                    reservation_id, user_id, reservation.amount, reservation.slot_id, days)
                if ret is None:
                    raise NoSuchReservationException(reservation_id)
                elif ret["status"] == "already_confirmed":
                    raise ReservationAlreadyConfirmedException(reservation_id)
                elif ret["status"] == "user_mismatch":
                    raise UserMismatchException(user_id)
                elif ret["status"] == "days_not_enough":
                    raise DaysNotLeftEnoughException(days)
                elif ret["status"] == "not_found":
                    raise NoSuchReservationException(reservation_id)
                elif ret["status"] == "no_slot":
                    raise NoSuchSlotException(reservation.slot_id)

                return ret
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException() from None
                raise

    async def delete_unconfirmed(self, reservation_id: int, user_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret = await conn.fetchrow(
                """
                    WITH target AS (
                        SELECT * FROM reservations WHERE id = $1
                    ), deleted AS (
                        DELETE FROM reservations r
                        WHERE r.id = target.id AND r.user_id = $2 AND r.confirmed = FALSE
                        RETURNING r.id
                    )
                    SELECT 
                    COALESCE(d.id, t.id) AS id,
                    CASE
                        WHEN t.user_id != $2 THEN 'user_mismatch'
                        WHEN t.confirmed = TRUE THEN 'already_confirmed'
                        ELSE 'deleted'
                    END AS status
                    FROM target t
                    LEFT JOIN deleted d ON t.id = d.id
                """,
                reservation_id, user_id)
            if ret is None:
                raise NoSuchReservationException(reservation_id)
            elif ret["status"] == "already_confirmed":
                raise ReservationAlreadyConfirmedException(reservation_id)
            elif ret["status"] == "user_mismatch":
                raise UserMismatchException(user_id)

    # Only for admin
    async def confirm_by_id(self, reservation_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                ret = await conn.fetchrow("UPDATE reservations SET confirmed = $1 WHERE id = $2 RETURNING id", True,
                                          reservation_id)
                if ret is None:
                    raise NoSuchReservationException(reservation_id)
                return ret
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException() from None
                raise

    async def modify_from_admin(self, reservation_id: int, reservation: ReservationDto):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                ret = await conn.fetchrow(
                    "UPDATE reservations SET (amount, slot_id) = ($1, $2) WHERE id = $3 RETURNING id",
                    reservation.amount, reservation.slot_id, reservation_id)
                if ret is None:
                    raise NoSuchReservationException(reservation_id)
                return ret
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException() from None
                raise

    async def delete_from_admin(self, reservation_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret = await conn.fetchrow("DELETE FROM reservations WHERE id = $1 RETURNING id", reservation_id)
            if ret is None:
                raise NoSuchReservationException(reservation_id)
            return ret
