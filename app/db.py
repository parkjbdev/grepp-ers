from typing import Optional
import asyncpg
import os
from asyncpg import Pool

from app.utils.decorators import singleton


@singleton
class Database:
    def __init__(self):
        self._pool: Optional[Pool] = None

    async def connect(self):
        print("connecting")
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL"),
                min_size=5,
                max_size=10,
                server_settings={'search_path': os.getenv("APP_DB_SCHEMA")}
            )

    async def disconnect(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    def get_pool(self) -> Pool:
        if self._pool is None:
            raise ConnectionError("DB Connection Failed.. Is connect() called?")
        return self._pool


db = Database()
