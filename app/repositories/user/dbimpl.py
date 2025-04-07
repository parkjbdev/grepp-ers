from asyncpg import Connection, Pool, PostgresError, UniqueViolationError

from app.repositories.user.exceptions import NoSuchUserException, UserNameAlreadyExistsException
from app.repositories.user.interface import UserRepository


class UserRepositoryImpl(UserRepository):
    def __init__(self, pool: Pool):
        self.__pool = pool

    async def find(self, username: str):
        async with self.__pool.acquire() as conn:  # type: Connection
            user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
            if user is None:
                raise NoSuchUserException(f"username = {username}")
            return user

    async def insert(self, username, hashed_password):
        async with self.__pool.acquire() as conn:  # type: Connection
            try:
                async with conn.transaction():
                    ret_id = await conn.fetchrow("INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                                                 username,
                                                 hashed_password)
                    if ret_id is None:
                        raise UserNameAlreadyExistsException(username)
                    return ret_id
            except UniqueViolationError as e:
                raise UserNameAlreadyExistsException(username)

    async def update_password(self, username: str, password: str):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret_id = await conn.fetchrow("UPDATE users SET password = $1 WHERE username = $2 RETURNING id",
                                         password,
                                         username)
            if ret_id is None:
                raise NoSuchUserException(f"username = {username}")
            return ret_id

    async def delete_by_username(self, username: str):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret_id = await conn.fetchrow("DELETE FROM users WHERE username = $1 RETURNING id", username)
            if ret_id is None:
                raise NoSuchUserException(f"username = {username}")
            return ret_id

    async def delete(self, userid: int):
        async with self.__pool.acquire() as conn:  # type: Connection
            ret_id = await conn.fetchrow("DELETE FROM users WHERE id = $1 RETURNING id", userid)
            if ret_id is None:
                raise NoSuchUserException(f"id = {userid}")
            return ret_id
