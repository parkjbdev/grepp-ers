from asyncpg import Connection, Pool, PostgresError, UniqueViolationError

from app.models.user_model import User
from app.repositories.user.interface import UserRepository


class UserRepositoryImpl(UserRepository):
    def __init__(self, pool: Pool):
        self.__pool = pool

    async def find(self, username: str):
        async with self.__pool.acquire() as conn:  # type: Connection
            return User(**dict(await conn.fetchrow("SELECT * FROM users WHERE username=$1", username)))

    async def insert(self, username, hashed_password):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                async with conn.transaction():
                    return await conn.execute("INSERT INTO users(username, password) VALUES($1, $2);", username,
                                              hashed_password)
            except UniqueViolationError as e:
                print(f"User with same username already exists: {e}")
            except PostgresError as e:
                print(f"PostgresERROR: {e}")

    async def update_password(self, username: str, password: str):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.execute("UPDATE users SET(password) = ($1) WHERE username = $2", password, username)

    async def delete_by_username(self, username: str):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.execute("DELETE users WHERE username=$1", username)

    async def delete(self, userid: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            return await conn.execute("DELETE users WHERE id=$1", userid)
