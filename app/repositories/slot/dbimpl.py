import logging
from datetime import datetime

from asyncpg import Connection, ExclusionViolationError, Pool

from app.models.slot_model import Slot
from app.repositories.slot.exceptions import SlotTimeRangeOverlapped
from app.repositories.slot.interface import SlotRepository


class SlotRepositoryImpl(SlotRepository):
    def __init__(self, pool: Pool):
        self.__pool = pool
        self.__logger = logging.getLogger(__name__)

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
            print(base_query)
            return await conn.fetch(base_query, *params)

    async def find_by_id(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            base_query = self.__base_query()
            base_query += "WHERE s.id = $1"
            base_query += "\nGROUP BY s.id, s.time_range"
            base_query += "\nORDER BY s.time_range"
            return await conn.fetchrow(base_query, slot_id)

    async def insert(self, slot: Slot):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                ret = await conn.execute("INSERT INTO slots(time_range) VALUES($1)", slot.time_range)
                affected_rows = int(ret.split()[-1])
                return affected_rows
            except ExclusionViolationError as e:
                self.__logger.exception(
                    f"Time slot conflict: The time range {slot.time_range} overlaps with an existing slot",
                    exc_info=False
                )
                raise SlotTimeRangeOverlapped(slot.time_range)

    async def modify(self, slot: Slot):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret = await conn.execute("UPDATE slots SET time_range = $1 WHERE id = $2", slot.time_range,
                                     slot.id)
            affected_rows = int(ret.split()[-1])
            return affected_rows

    async def delete(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret = await conn.execute("DELETE FROM slots WHERE id = $1", slot_id)
            affected_rows = int(ret.split()[-1])
            return affected_rows
