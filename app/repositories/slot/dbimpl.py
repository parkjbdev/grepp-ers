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

    async def find(self):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetch("SELECT * FROM slots")

    async def find_by_time_range(self, start_at: datetime, end_at: datetime):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetch("SELECT * FROM slots WHERE time_range && TSTZRANGE($1, $2)", start_at, end_at)

    async def find_by_id(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetchrow("SELECT * FROM slots WHERE id = $1", slot_id)

    async def insert(self, slot: Slot):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                return await conn.execute("INSERT INTO slots(time_range) VALUES($1)", slot.time_range)
            except ExclusionViolationError as e:
                self.__logger.exception(
                    f"Time slot conflict: The time range {slot.time_range} overlaps with an existing slot",
                    exc_info=False
                )
                raise SlotTimeRangeOverlapped(slot.time_range)

    async def modify(self, slot: Slot):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.execute("UPDATE slots SET(time_range) = ($1) WHERE id = $2", slot.time_range, slot.id)

    async def delete(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.execute("DELETE slots WHERE id = $1", slot_id)

    async def count_confirmed_slot(self):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetch("""
                SELECT s.id AS slot_id, s.time_range, COUNT(CASE WHEN r.confirmed = TRUE THEN r.id ELSE NULL END) AS amount 
                FROM slots AS s LEFT JOIN reservations AS r ON r.slot_id = s.id
                GROUP BY s.id, s.time_range
                ORDER BY s.time_range
            """)
