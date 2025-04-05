from asyncpg import Connection, Pool

from app.models.slot_model import Slot
from app.repositories.slot.interface import SlotRepository


class SlotRepositoryImpl(SlotRepository):
    def __init__(self, pool: Pool):
        self.__pool = pool

    async def find(self):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetch("SELECT * FROM slots")

    async def find_by_id(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.fetchrow("SELECT * FROM slots WHERE id = $1", slot_id)

    async def insert(self, slot: Slot):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.execute("INSERT INTO slots(time_range) VALUES($1)", slot.time_range)

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
