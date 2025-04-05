import logging
import os
from logging import Logger
from typing import Optional

import asyncpg
from asyncpg import Pool

from app.database.interface import Database
from app.utils.decorators import singleton


@singleton
class ExamReservationSystemDatabase(Database):
    def __init__(self):
        self.__pool: Optional[Pool] = None
        self.__logger: Logger = logging.getLogger(__name__)

    async def connect(self):
        if self.__pool is None:
            self.__logger.info("Connecting to the database...")
            try:
                self.__pool = await asyncpg.create_pool(
                    os.getenv("DATABASE_URL"),
                    min_size=5,
                    max_size=10,
                    server_settings={'search_path': os.getenv("APP_DB_SCHEMA")}
                )
            except asyncpg.PostgresError as e:
                self.__logger.exception("Failed to connect to the database.")
                raise
            except Exception as e:
                self.__logger.exception(f"Unknown Exception: {e}")
                raise
            self.__logger.info("Connected to the database.")

    async def disconnect(self):
        if self.__pool:
            self.__logger.info("Disconnecting from the database...")
            try:
                await self.__pool.close()
                self.__logger.info("Disconnected from the database.")
            except Exception as e:
                self.__logger.exception(f"Failed to disconnect from the database: {e}")
                raise
            self.__pool = None
        else:
            self.__logger.warning("No active database connection to disconnect.")

    def get_pool(self) -> Pool:
        if self.__pool is None:
            raise ConnectionError("DB Connection Failed.. Is connect() called?")
        return self.__pool
