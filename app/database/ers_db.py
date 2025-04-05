import logging
import os
from logging import Logger
from typing import Optional

import asyncpg
from asyncpg import Pool

__pool: Optional[Pool] = None
__logger: Logger = logging.getLogger(__name__)


async def connect():
    global __pool
    if __pool is None:
        __logger.info("Connecting to the database...")
        try:
            __pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL"),
                min_size=5,
                max_size=10,
                server_settings={'search_path': os.getenv("APP_DB_SCHEMA")}
            )
        except asyncpg.PostgresError as e:
            __logger.exception("Failed to connect to the database.")
            raise
        except Exception as e:
            __logger.exception(f"Unknown Exception: {e}")
            raise
        __logger.info("Connected to the database.")


async def disconnect():
    global __pool
    if __pool:
        __logger.info("Disconnecting from the database...")
        try:
            await __pool.close()
            __logger.info("Disconnected from the database.")
        except Exception as e:
            __logger.exception(f"Failed to disconnect from the database: {e}")
            raise
        __pool = None
    else:
        __logger.warning("No active database connection to disconnect.")


def get_pool() -> Pool:
    global __pool
    if __pool is None:
        raise ConnectionError("DB Connection Failed.. Is connect() called?")
    return __pool
