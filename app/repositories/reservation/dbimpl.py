from datetime import datetime
from typing import Optional

from asyncpg import Connection, Pool, PostgresError

from app.models.reservation_model import Reservation, ReservationDto
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.repositories.reservation.interface import ReservationRepository


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
            return row

    async def find_reservation_by_slot(self, slot_id: int, confirmed: bool):
        base_query = self.__joined_query()
        base_query += "\nWHERE slot_id = $1 AND confirmed = $2"
        async with self.__pool.acquire() as conn:
            row = await conn.fetchrow(base_query, slot_id, confirmed)
            return row

    async def insert(self, reservation: Reservation):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                res = await conn.execute(
                    "INSERT INTO reservations(slot_id, user_id, amount) VALUES($1, $2, $3)",
                    reservation.slot_id, reservation.user_id, reservation.amount)
                affected_rows = int(res.split()[-1])
                return affected_rows
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException()
                raise

    # Only for admin
    async def confirm_by_id(self, reservation_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                res = await conn.execute("UPDATE reservations SET confirmed = $1 WHERE id = $2", True, reservation_id)
                affected_rows = int(res.split()[-1])
                if affected_rows == 0:
                    raise KeyError(f"Reservation not found: {reservation_id}")
                return affected_rows
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException()
                raise

    async def modify(self, id: int, reservation: ReservationDto, user_id: Optional[int] = None):
        # TODO: 에러 핸들링 섬세하게... confirmed 여부에 따라 다르게
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                if user_id is not None:
                    res = await conn.execute(
                        "UPDATE reservations SET (amount, slot_id) = ($1, $2) WHERE id = $3 AND user_id = $4 AND confirmed = FALSE",
                        reservation.amount, reservation.slot_id, id, user_id)
                else:
                    res = await conn.execute("UPDATE reservations SET (amount, slot_id) = ($1, $2) WHERE id = $3",
                                             reservation.amount, reservation.slot_id, id)
                affected_rows = int(res.split()[-1])
                if affected_rows == 0:
                    raise KeyError(f"Reservation not found: {id}")
                return affected_rows
            except PostgresError as e:
                if "SlotLimitExceeded" in str(e):
                    raise SlotLimitExceededException()
                raise

    async def delete(self, reservation_id: int, user_id: Optional[int] = None):
        async with self.__pool.acquire() as conn:  # type: Connection
            if user_id is not None:
                res = await conn.execute(
                    "DELETE FROM reservations WHERE id = $1 AND user_id = $2 AND confirmed = FALSE", reservation_id,
                    user_id)
            else:
                res = await conn.execute("DELETE FROM reservations WHERE id = $1", reservation_id)

            affected_rows = int(res.split()[-1])
            if affected_rows == 0:
                raise KeyError(f"Reservation not found: {reservation_id}")
            return affected_rows
