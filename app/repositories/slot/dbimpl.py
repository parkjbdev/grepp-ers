from abc import ABC, abstractmethod
from typing import Annotated

from asyncpg import Connection
from fastapi import Depends

from app.database.interface import Database
from app.dependencies.config import database
from app.models.slot_model import Slot
from app.repositories.slot.interface import SlotRepository
from app.utils.decorators import singleton



@singleton
class SlotRepositoryImpl(SlotRepository):
    def __init__(self, db: Annotated[Database, Depends(lambda: database())]):
        self.__pool = db.get_pool()

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
            return conn.execute("UPDATE slots SET(time_range) = ($1) WHERE id = $2", slot.time_range, slot.id)

    async def delete(self, slot_id: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            return conn.execute("DELETE slots WHERE id = $1", slot_id)
