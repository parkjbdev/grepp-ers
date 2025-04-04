from typing import Annotated

from asyncpg import Connection, PostgresError, UniqueViolationError
from fastapi import Depends

from app.database.interface import Database
from app.dependencies.config import database
from app.repositories.user.interface import UserRepository
from app.utils.decorators import singleton


@singleton
class UserRepositoryImpl(UserRepository):
    def __init__(self, db: Annotated[Database, Depends(lambda: database())]):
        self.pool = db.get_pool()

    async def find(self, username: str):
        async with self.pool.acquire() as conn:  # type: Connection
            return await conn.fetchrow("SELECT * FROM users WHERE username=$1", username)

    async def insert(self, username, hashed_password):
        async with self.pool.acquire() as conn:  # type: Connection
            try:
                async with conn.transaction():
                    await conn.execute("INSERT INTO users(username, password) VALUES($1, $2);", username,
                                       hashed_password)
            except UniqueViolationError as e:
                print(f"User with same username already exists: {e}")
            except PostgresError as e:
                print(f"PostgresERROR: {e}")

    async def delete_by_username(self, username: str):
        async with self.pool.acquire() as conn:  # type: Connection
            return await conn.execute("DELETE users WHERE username=$1", username)

    async def delete(self, userid: int):
        async with self.pool.acquire() as conn:  # type: Connection
            return await conn.execute("DELETE users WHERE id=$1", userid)
