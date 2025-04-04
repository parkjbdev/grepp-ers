from typing import Optional
import asyncpg
import os

from asyncpg import Pool

from app.database.interface import Database
from app.utils.decorators import singleton


@singleton
class ExamReservationSystemDatabase(Database):
    def __init__(self):
        self.__pool: Optional[Pool] = None

    async def connect(self):
        print("connecting")
        if self.__pool is None:
            self.__pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL"),
                min_size=5,
                max_size=10,
                server_settings={'search_path': os.getenv("APP_DB_SCHEMA")}
            )

    async def disconnect(self):
        if self.__pool:
            await self.__pool.close()
            self.__pool = None

    def get_pool(self) -> Pool:
        if self.__pool is None:
            raise ConnectionError("DB Connection Failed.. Is connect() called?")
        return self.__pool
