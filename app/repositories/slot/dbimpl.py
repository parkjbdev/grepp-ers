from datetime import datetime

from asyncpg import Connection, ExclusionViolationError, Pool, PostgresError

from app.models.slot_model import Slot
from app.repositories.slot.exceptions import NoSuchSlotException, SlotTimeRangeOverlapped
from app.repositories.slot.interface import SlotRepository


class SlotRepositoryImpl(SlotRepository):
    def __init__(self, pool: Pool):
        self.__pool = pool

    @staticmethod
    def __base_query():
        return """
                SELECT s.id AS id, s.time_range AS time_range, COALESCE(SUM(r.amount), 0) AS amount 
                FROM slots AS s LEFT JOIN reservations AS r ON r.slot_id = s.id AND r.confirmed = TRUE
            """

    async def find(self, start_at: datetime = None, end_at: datetime = None):
        async with self.__pool.acquire() as conn:  # type: Connection
            conditions = []
            params = []
            if start_at is not None and end_at is not None:
                params.extend([start_at, end_at])
                conditions.append(f"s.time_range && TSTZRANGE(${len(params) - 1}, ${len(params)})")
            elif start_at is not None:
                params.append(start_at)
                conditions.append(f"UPPER(s.time_range) >= ${len(params)}")
            elif end_at is not None:
                params.append(end_at)
                conditions.append(f"LOWER(s.time_range) <= ${len(params)}")
            base_query = self.__base_query()
            if conditions:
                base_query += "\nWHERE " + " AND ".join(conditions)
            base_query += "\nGROUP BY s.id, s.time_range"
            base_query += "\nORDER BY s.time_range"

            return await conn.fetch(base_query, *params)

    async def find_by_id(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            base_query = self.__base_query()
            base_query += "WHERE s.id = $1"
            base_query += "\nGROUP BY s.id, s.time_range"
            base_query += "\nORDER BY s.time_range"

            ret = await conn.fetchrow(base_query, slot_id)
            if ret is None:
                raise NoSuchSlotException(slot_id)

    async def insert(self, slot: Slot):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                return await conn.fetchrow("INSERT INTO slots(time_range) VALUES($1) RETURNING id", slot.time_range)
            except ExclusionViolationError as e:
                raise SlotTimeRangeOverlapped(slot.time_range) from None

    async def modify(self, slot: Slot):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret = await conn.fetchrow("UPDATE slots SET time_range = $1 WHERE id = $2 RETURNING id", slot.time_range,
                                      slot.id)
            if ret is None:
                raise NoSuchSlotException(slot.id)
            return ret

    async def delete(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret = await conn.fetchrow("DELETE FROM slots WHERE id = $1 RETURNING id", slot_id)
            if ret is None:
                raise NoSuchSlotException(slot_id)
            return ret
